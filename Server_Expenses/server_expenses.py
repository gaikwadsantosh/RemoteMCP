from fastmcp import FastMCP
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

init_db()

@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.

    Args:
        date (str): The date of the expense in YYYY-MM-DD format.
        amount (float): The amount of the expense.
        category (str): The primary category of the expense.
        subcategory (str, optional): The subcategory of the expense. Defaults to "".
        note (str, optional): Additional notes about the expense. Defaults to "".
    '''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return {"status": "ok", "id": cur.lastrowid}
    
@mcp.tool()
def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.

    Args:
        start_date (str): The start date of the range in YYYY-MM-DD format.
        end_date (str): The end date of the range in YYYY-MM-DD format.

    Returns:
        list: A list of dictionaries, each representing an expense.
    '''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.

    Args:
        start_date (str): The start date of the range in YYYY-MM-DD format.
        end_date (str): The end date of the range in YYYY-MM-DD format.
        category (str, optional): Filter by a specific category. Defaults to None.

    Returns:
        list: A list of dictionaries containing category and total_amount.
    '''
    with sqlite3.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def update_expense(id: int, date: str = None, amount: float = None, category: str = None, subcategory: str = None, note: str = None):
    '''Update an existing expense by its ID.

    Args:
        id (int): The ID of the expense to update.
        date (str, optional): New date in YYYY-MM-DD format.
        amount (float, optional): New amount.
        category (str, optional): New category.
        subcategory (str, optional): New subcategory.
        note (str, optional): New note.

    Returns:
        dict: A status message indicating success or failure.
    '''
    with sqlite3.connect(DB_PATH) as c:
        fields = []
        values = []
        if date is not None:
            fields.append("date = ?")
            values.append(date)
        if amount is not None:
            fields.append("amount = ?")
            values.append(amount)
        if category is not None:
            fields.append("category = ?")
            values.append(category)
        if subcategory is not None:
            fields.append("subcategory = ?")
            values.append(subcategory)
        if note is not None:
            fields.append("note = ?")
            values.append(note)
        
        if not fields:
            return {"status": "error", "message": "No fields provided for update"}
        
        values.append(id)
        query = f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?"
        
        cur = c.execute(query, tuple(values))
        if cur.rowcount == 0:
             return {"status": "error", "message": f"Record with id {id} not found"}
        
        return {"status": "ok", "updated_id": id}

@mcp.tool()
def delete_expense(id: int):
    '''Delete an expense from the database by its ID.

    Args:
        id (int): The ID of the expense to delete.

    Returns:
        dict: A status message indicating success or failure.
    '''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("DELETE FROM expenses WHERE id = ?", (id,))
        if cur.rowcount == 0:
            return {"status": "error", "message": f"Record with id {id} not found"}
        return {"status": "ok", "deleted_id": id}

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    #mcp.run() #default stdio transport
    mcp.run(transport="http", host="0.0.0.0", port=8000) #http transport on port 8000 by default
