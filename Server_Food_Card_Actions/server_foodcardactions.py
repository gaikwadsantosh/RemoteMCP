from fastmcp import FastMCP
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "FoodCardActions.db")

mcp = FastMCP("FoodCardTracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS cardactions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                cardnumber TEXT NOT NULL,
                cardaction TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

init_db()

@mcp.tool()
def add_card_action(date, cardnumber, cardaction, note=""):
    '''Add a new food card action to the database.

    Args:
        date (str): The date of the transaction in YYYY-MM-DD format.
        cardnumber (str): The identifier for the food card.
        cardaction (str): The type of action (e.g., 'RELOAD', 'SPEND').
        note (str, optional): Additional notes about the transaction. Defaults to "".
    '''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO cardactions(date, cardnumber, cardaction, note) VALUES (?,?,?,?)",
            (date, cardnumber, cardaction, note)
        )
        return {"status": "ok", "id": cur.lastrowid}
    
@mcp.tool()
def list_card_actions(start_date, end_date):
    '''List food card entries within an inclusive date range.

    Args:
        start_date (str): The start date of the range in YYYY-MM-DD format.
        end_date (str): The end date of the range in YYYY-MM-DD format.

    Returns:
        list: A list of dictionaries, each representing a card action.
    '''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, cardnumber, cardaction, note
            FROM cardactions
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def update_card_action(id: int, date: str = None, cardnumber: str = None, cardaction: str = None, note: str = None):
    '''Update an existing food card action by its ID.

    Args:
        id (int): The ID of the record to update.
        date (str, optional): New date in YYYY-MM-DD format.
        cardnumber (str, optional): New card number.
        cardaction (str, optional): New action type.
        note (str, optional): New note.

    Returns:
        dict: A status message indicating success or failure.
    '''
    with sqlite3.connect(DB_PATH) as c:
        # Construct the UPDATE query dynamically based on provided fields
        fields = []
        values = []
        if date is not None:
            fields.append("date = ?")
            values.append(date)
        if cardnumber is not None:
            fields.append("cardnumber = ?")
            values.append(cardnumber)
        if cardaction is not None:
            fields.append("cardaction = ?")
            values.append(cardaction)
        if note is not None:
            fields.append("note = ?")
            values.append(note)
        
        if not fields:
            return {"status": "error", "message": "No fields provided for update"}
        
        values.append(id)
        query = f"UPDATE cardactions SET {', '.join(fields)} WHERE id = ?"
        
        cur = c.execute(query, tuple(values))
        if cur.rowcount == 0:
             return {"status": "error", "message": f"Record with id {id} not found"}
        
        return {"status": "ok", "updated_id": id}

@mcp.tool()
def delete_card_action(id: int):
    '''Delete a food card action from the database by its ID.

    Args:
        id (int): The ID of the record to delete.

    Returns:
        dict: A status message indicating success or failure.
    '''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("DELETE FROM cardactions WHERE id = ?", (id,))
        if cur.rowcount == 0:
            return {"status": "error", "message": f"Record with id {id} not found"}
        return {"status": "ok", "deleted_id": id}

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001) #http transport on port 8001 by default
