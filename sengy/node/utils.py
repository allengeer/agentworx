from datetime import datetime
from typing import List

from dateutil.relativedelta import relativedelta
from langchain.docstore.document import Document
from langchain.tools import BaseTool
from langchain_core.tools import BaseToolkit, tool
from langgraph.graph.message import MessagesState  # Import MessagesState


class DateTimeToolkit(BaseToolkit):
    """Toolkit for date-related operations. This toolkit provides tools to get the user's current date in their current location. It also provides complex date computations."""
    def get_tools(self) -> List[BaseTool]:
        return [
            get_todays_date,
            get_todays_datetime,
            get_current_time,
            is_leap_year,
            delta,
            add_delta
        ]

@tool
def get_todays_date() -> str:
    """Returns today's date in YYYY-MM-DD format in the location of the user."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

@tool
def get_todays_datetime() -> str:
    """Returns today's date and time in YYYY-MM-DD HH:MM:SS format in the location of the user."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def get_current_time() -> str:
    """Returns the current time in HH:MM:SS format in the location of the user."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

@tool
def is_leap_year(year: int) -> bool:
    """Checks if the given year is a leap year."""
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        return True
    return False

@tool
def delta(start_date: str, end_date: str, unit: str) -> str:
    """Calculates the difference between two dates in the specified unit (days, weeks, months, years)."""
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    if unit == "days":
        return str((end - start).days)
    elif unit == "weeks":
        return str((end - start).days // 7)
    elif unit == "months":
        delta = relativedelta(end, start)
        return f"{delta.years * 12 + delta.months} months"
    elif unit == "years":
        delta = relativedelta(end, start)
        return f"{delta.years} years"
    else:
        raise ValueError("Invalid unit. Use 'days', 'weeks', 'months', or 'years'.")
    
@tool
def add_delta(start_date: str, delta: int, unit: str) -> str:
    """Adds a delta to a date in the specified unit (days, weeks, months, years)."""
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    
    if unit == "days":
        new_date = start + relativedelta(days=delta)
    elif unit == "weeks":
        new_date = start + relativedelta(weeks=delta)
    elif unit == "months":
        new_date = start + relativedelta(months=delta)
    elif unit == "years":
        new_date = start + relativedelta(years=delta)
    else:
        raise ValueError("Invalid unit. Use 'days', 'weeks', 'months', or 'years'.")
    
    return new_date.strftime("%Y-%m-%d")
    
