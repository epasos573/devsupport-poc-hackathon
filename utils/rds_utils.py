import logging
import mysql.connector

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union

from utils.boto3_utils import SSM
from mysql.connector import errorcode, cursor


class RDSUtils:
    """
    A utility class for managing a connection to an RDS MySQL database
    and providing convenience methods for database operations.
    """

    def __init__(self) -> None:
        """
        Initializes the RDSUtils instance with no active connection.
        The connection is established lazily upon need.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self._connection: Optional[mysql.connector.connection.MySQLConnection] = None

    def create_rds_connection(self) -> None:
        """
        Creates and stores a MySQL connection using credentials and
        configuration from AWS SSM Parameter Store. If a connection
        already exists and is open, this method does nothing.
        """
        if self._connection and self._connection.is_connected():
            # Already have a valid connection
            return

        try:
            self._connection = mysql.connector.connect(
                user=SSM.get_secret('rds_username'),
                password=SSM.get_secret('rds_password'),
                host=SSM.get_secret('rds_host'),
                database=SSM.get_secret('rds_scheme')
            )
            self.logger.info("RDS connection created successfully.")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                self.logger.error(f"Invalid username or password: {err}")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                self.logger.error("Database does not exist.")
            else:
                self.logger.error(f"Error creating RDS connection: {err}")

    def create_cursor(self) -> Optional[cursor.MySQLCursorDict]:
        """
        Creates a MySQL dictionary cursor from the current connection.

        :return: A MySQL dictionary cursor if successful, or None if not.
        """
        try:
            self.create_rds_connection()  # Ensure connection is established
            if self._connection and self._connection.is_connected():
                return self._connection.cursor(dictionary=True)
        except mysql.connector.Error as err:
            self.logger.error(f"Error creating cursor: {err}")
        return None

    def close_cursor(self, db_cursor: Optional[cursor.MySQLCursorDict]) -> None:
        """
        Closes the provided cursor if the underlying connection is still valid.

        :param db_cursor: The cursor to close.
        """
        if not db_cursor:
            return
        try:
            db_cursor.close()
        except mysql.connector.Error as err:
            self.logger.error(f"Error closing cursor: {err}")

    def close_connection(self) -> None:
        """
        Closes the current database connection if it is open.
        """
        try:
            if self._connection and self._connection.is_connected():
                self._connection.close()
                self.logger.info("RDS connection closed successfully.")
        except mysql.connector.Error as err:
            self.logger.error(f"Error closing connection: {err}")

    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """
        Inserts a new row into a given table using parameterized queries.

        :param table_name: Name of the table to insert into.
        :param data: A dictionary where keys are column names and values are the
                     values to be inserted.
        :return: The ID of the newly inserted row if successful, -1 otherwise.
                 Note: For tables without an AUTO_INCREMENT primary key,
                 this may return 0 even if successful.
        """
        self.create_rds_connection()
        if not self._connection or not self._connection.is_connected():
            self.logger.error("No active RDS connection for insert operation.")
            return -1

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        values = list(data.values())

        db_cursor = self.create_cursor()
        if not db_cursor:
            return -1

        try:
            db_cursor.execute(sql, values)
            self._connection.commit()
            # lastrowid might be 0 for non-AUTO_INCREMENT tables
            return db_cursor.lastrowid
        except mysql.connector.Error as err:
            self.logger.error(f"Insert error in table '{table_name}': {err}")
            return -1
        finally:
            self.close_cursor(db_cursor)

    def update(self, table_name: str, data: Dict[str, Any], condition: str,
               condition_params: Optional[Tuple[Any, ...]] = None) -> int:
        """
        Updates existing rows in a given table based on a parameterized condition.

        :param table_name: Name of the table to update.
        :param data: A dictionary where keys are column names and values are the
                     new values to be updated.
        :param condition: A string specifying the WHERE clause with placeholders (e.g., "id = %s").
        :param condition_params: A tuple of values corresponding to the placeholders in condition.
        :return: The number of rows affected if successful, -1 otherwise.
        """
        self.create_rds_connection()
        if not self._connection or not self._connection.is_connected():
            self.logger.error("No active RDS connection for update operation.")
            return -1

        set_clause = ", ".join([f"{col} = %s" for col in data.keys()])
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        # Combine data values with condition parameters
        params: List[Any] = list(data.values())
        if condition_params:
            params.extend(condition_params)

        db_cursor = self.create_cursor()
        if not db_cursor:
            return -1

        try:
            db_cursor.execute(sql, tuple(params))
            self._connection.commit()
            return db_cursor.rowcount
        except mysql.connector.Error as err:
            self.logger.error(f"Update error in table '{table_name}': {err}")
            return -1
        finally:
            self.close_cursor(db_cursor)

    def select(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
        """
        Performs a generic SELECT query using a parameterized statement and returns all matching rows.

        :param query: The SELECT statement to execute (e.g., "SELECT * FROM table WHERE col = %s").
        :param params: A tuple of parameter values to bind to the placeholders in the query.
        :return: A list of dictionaries representing the rows, or an empty list if no rows or error.
        """
        self.create_rds_connection()
        if not self._connection or not self._connection.is_connected():
            self.logger.error("No active RDS connection for select operation.")
            return []

        db_cursor = self.create_cursor()
        if not db_cursor:
            return []

        try:
            # If params is None, we pass an empty tuple for safety
            db_cursor.execute(query, params if params else ())
            return db_cursor.fetchall()  # Each row is a dict
        except mysql.connector.Error as err:
            self.logger.error(f"Select error: {err}")
            return []
        finally:
            self.close_cursor(db_cursor)

    def delete(self, table_name: str, condition: str, params: Optional[Tuple[Any, ...]] = None) -> int:
        """
        Deletes rows from a given table based on a parameterized condition.

        :param table_name: Name of the table to delete from.
        :param condition: A string specifying the WHERE clause with placeholders (e.g., "id = %s").
        :param params: A tuple of parameter values to bind to the placeholders in the condition.
        :return: The number of rows affected if successful, -1 otherwise.
        """
        self.create_rds_connection()
        if not self._connection or not self._connection.is_connected():
            self.logger.error("No active RDS connection for delete operation.")
            return -1

        sql = f"DELETE FROM {table_name} WHERE {condition}"

        db_cursor = self.create_cursor()
        if not db_cursor:
            return -1

        try:
            db_cursor.execute(sql, params if params else ())
            self._connection.commit()
            return db_cursor.rowcount
        except mysql.connector.Error as err:
            self.logger.error(f"Delete error in table '{table_name}': {err}")
            return -1
        finally:
            self.close_cursor(db_cursor)

    def insert_ai_agent_review(
        self,
        ticket_id: int,
        agent_id: int,
        resolution: int,
        engagement: int,
        clarity: int,
        throughout_sentiment: int,
        end_sentiment: Optional[int],
        highlights: str,
        improvements: str
    ) -> int:
        """
        Inserts a new record into the ai_agent_review table.

        :param ticket_id: The Zendesk ticket ID.
        :param agent_id: The ID of the agent's Zendesk user.
        :param resolution: A 1-5 score for how much of the inquiry was resolved.
        :param engagement: A 1-5 score reflecting the engagement level of the agent.
        :param clarity: A 1-5 score of how clear the agent's responses were.
        :param throughout_sentiment: A 1-5 score reflecting the average customer sentiment
                                     up to the agent's last reply.
        :param end_sentiment: A 1-5 score reflecting the sentiment of the customer after
                              the agent's last reply (can be NULL).
        :param highlights: Free-text feedback on what the agent did well.
        :param improvements: Free-text feedback on what the agent could improve.
        :return: The new row's ID (which may be 0 if the table does not use AUTO_INCREMENT),
                 or -1 on error.
        """
        data = {
            "TICKET_ID": ticket_id,
            "AGENT_ID": agent_id,
            "RESOLUTION": resolution,
            "ENGAGEMENT": engagement,
            "CLARITY": clarity,
            "THROUGHOUT_SENTIMENT": throughout_sentiment,
            "END_SENTIMENT": end_sentiment,
            "HIGHLIGHTS": highlights,
            "IMPROVEMENTS": improvements
        }
        return self.insert("ai_agent_review", data)

    def select_ai_agent_review(
        self,
        ticket_id: int,
        agent_id: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieves rows from the ai_agent_review table for a given ticket_id and agent_id.

        :param ticket_id: The Zendesk ticket ID to filter on.
        :param agent_id: The agent's Zendesk user ID to filter on.
        :return: A list of matching rows as dictionaries. Will return an empty list if no match.
        """
        sql = """
            SELECT * 
            FROM ai_agent_review
            WHERE TICKET_ID = %s AND AGENT_ID = %s
        """
        return self.select(sql, (ticket_id, agent_id))

    def insert_ai_ticket_review(
        self,
        ticket_id: int,
        resolution: int,
        engagement: int,
        clarity: int,
        throughout_sentiment: int,
        end_sentiment: Optional[int],
        highlights: str,
        improvements: str
    ) -> int:
        """
        Inserts a new record into the ai_ticket_review table.

        :param ticket_id: The Zendesk ticket ID (unique for macro evaluations).
        :param resolution: A 1-5 score for how much of the inquiry was resolved.
        :param engagement: A 1-5 score reflecting the engagement level/tone of the team.
        :param clarity: A 1-5 score of how clear the team's responses were.
        :param throughout_sentiment: A 1-5 score reflecting the average sentiment of the customer
                                     throughout the ticket.
        :param end_sentiment: A 1-5 score reflecting the sentiment of the customer upon resolution
                              (can be NULL).
        :param highlights: Free-text feedback on what was done well in handling the ticket.
        :param improvements: Free-text feedback on what could be improved in handling the ticket.
        :return: The new row's ID (which may be 0 if the table does not use AUTO_INCREMENT),
                 or -1 on error.
        """
        data = {
            "TICKET_ID": ticket_id,
            "RESOLUTION": resolution,
            "ENGAGEMENT": engagement,
            "CLARITY": clarity,
            "THROUGHOUT_SENTIMENT": throughout_sentiment,
            "END_SENTIMENT": end_sentiment,
            "HIGHLIGHTS": highlights,
            "IMPROVEMENTS": improvements
        }
        return self.insert("ai_ticket_review", data)

    def select_ai_ticket_review(
        self,
        ticket_id: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieves rows from the ai_ticket_review table for a given ticket_id.

        :param ticket_id: The Zendesk ticket ID to filter on.
        :return: A list of matching rows as dictionaries. Will return an empty list if no match.
        """
        sql = """
            SELECT *
            FROM ai_ticket_review
            WHERE TICKET_ID = %s
        """
        return self.select(sql, (ticket_id,))
