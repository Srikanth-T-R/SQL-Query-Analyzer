from flask import Flask, render_template, request
import sqlite3
import time

# Initialize Flask
app = Flask(__name__)

# Function to detect SQL issues(unbounded loops, Cartesian products, nested subqueries)
def detect_unbounded_loop(query):
    warnings = []
    
    # Check for recursive CTEs
    if "WITH RECURSIVE" in query.upper() and "UNION ALL" in query.upper():
        if "WHERE" in query.upper() or "LIMIT" in query.upper():
            warnings.append("Recursive CTE detected with termination condition. Review for safety.")
        else:
            warnings.append("Potential unbounded recursion in recursive CTE.")
    
    # Check for Cartesian products
    if "," in query and "JOIN" not in query.upper():
        warnings.append("Potential Cartesian product detected.")
    
    # Check for nested subqueries
    if "SELECT" in query.upper() and "(" in query and ")" in query and "WITH RECURSIVE" not in query.upper():
        warnings.append("Nested subquery detected. Check for constraints.")
    
    return warnings

# Function to execute SQL queries
def execute_query(cursor, query):
    try:
        start_time = time.time()
        cursor.execute(query)
        rows = cursor.fetchall()
        execution_time = time.time() - start_time
        
        # Warn if query execution takes too long
        if execution_time > 2:
            return f"Execution took {execution_time:.2f} seconds. Query might be unbounded."
        return f"Executed successfully in {execution_time:.2f} seconds. Rows fetched: {len(rows)}"
    except sqlite3.OperationalError as e:
        return f"Execution failed: {e}"

# Function to set up the SQLite database
def setup_database(cursor):
    # Create sample tables and insert test data
    cursor.execute("CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT);")
    cursor.execute("INSERT INTO employees (name) VALUES ('Alice'), ('Bob');")
    cursor.execute("CREATE TABLE table1 (id INTEGER PRIMARY KEY, value TEXT);")
    cursor.execute("CREATE TABLE table2 (id INTEGER PRIMARY KEY, value TEXT);")
    cursor.execute("INSERT INTO table1 (value) VALUES ('A'), ('B');")
    cursor.execute("INSERT INTO table2 (value) VALUES ('X'), ('Y');")

# Home route for the web application
@app.route("/", methods=["GET", "POST"])
def home():
    query = ""
    warnings = []
    execution_result = ""

    if request.method == "POST":
        # Retrieve the SQL query from the form
        query = request.form["query"]
        warnings = detect_unbounded_loop(query)  # Analyze the query for potential issues

        # Set up an in-memory SQLite database
        connection = sqlite3.connect(":memory:")
        cursor = connection.cursor()
        setup_database(cursor)  # Create sample tables and data
        connection.commit()

        # Execute the query and capture the result
        execution_result = execute_query(cursor, query)

        # Close the database connection
        connection.close()

    # Render the HTML template with query results
    return render_template("index.html", query=query, warnings=warnings, execution_result=execution_result)

# Run the application in debug mode
if __name__ == "__main__":
    app.run(debug=True)
