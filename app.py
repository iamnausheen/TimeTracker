import datetime
from flask import Flask, render_template, request

app = Flask(__name__)

# Define fixed time requirements in minutes for clarity
REQUIRED_TOTAL_OFFICE_MINUTES = 9 * 60  # 9 hours total in the office
REQUIRED_WORK_MINUTES = (7 * 60) + 30   # 7 hours 30 minutes of actual work
DESIGNATED_BREAK_MINUTES = (1 * 60) + 30 # 1 hour 30 minutes designated break

@app.route('/', methods=['GET'])
def index():
    """
    Renders the main HTML page with the time input form.
    This is the entry point for the web application.
    """
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate_time():
    """
    Handles the form submission, calculates employee times based on arrival
    and break time spent, and determines compliance with office rules.
    """
    # Retrieve input values from the form
    arrival_time_str = request.form.get('arrival_time')
    break_time_spent_str = request.form.get('break_time_spent')

    # Initialize variables that will hold the calculated results and status
    required_departure_time_display = None
    break_time_spent_display = None
    break_time_left_display = None
    effective_work_time_display = None
    status_message = ""
    status_color = "text-gray-700" # Default text color for status messages

    try:
        # Parse the arrival time string into a datetime.time object
        arrival_time = datetime.datetime.strptime(arrival_time_str, '%H:%M').time()

        # Parse the break time spent string (e.g., "01:30" for 1 hour 30 minutes)
        # It expects HH:MM format due to the 'pattern' attribute in the HTML input
        break_h, break_m = map(int, break_time_spent_str.split(':'))
        break_time_spent_minutes = break_h * 60 + break_m

        # Define the allowed flexible arrival time window
        min_arrival_time_allowed = datetime.time(8, 0)  # 08:00 AM
        max_arrival_time_allowed = datetime.time(10, 0) # 10:00 AM

        # Validate if the entered arrival time falls within the allowed range
        if not (min_arrival_time_allowed <= arrival_time <= max_arrival_time_allowed):
            status_message = "Error: Arrival time must be between 08:00 AM and 10:00 AM."
            status_color = "text-red-600" # Indicate an error with red text
        else:
            # Create a dummy datetime object for accurate time arithmetic.
            # The date part (2000, 1, 1) is arbitrary as only time differences matter.
            dummy_date = datetime.date(2000, 1, 1)
            arrival_datetime_obj = datetime.datetime.combine(dummy_date, arrival_time)

            # Calculate the required departure time.
            # Employees must complete 9 hours total in the office.
            required_departure_datetime_obj = arrival_datetime_obj + \
                                              datetime.timedelta(minutes=REQUIRED_TOTAL_OFFICE_MINUTES)
            # Format the calculated departure time for display (HH:MM)
            required_departure_time_display = required_departure_datetime_obj.strftime('%H:%M')

            # Calculate the remaining break time.
            break_time_left_minutes = DESIGNATED_BREAK_MINUTES - break_time_spent_minutes
            
            # Calculate the effective work time if the employee stays for the
            # full REQUIRED_TOTAL_OFFICE_MINUTES (9 hours).
            # This is total time minus the actual break time spent.
            effective_work_minutes = REQUIRED_TOTAL_OFFICE_MINUTES - break_time_spent_minutes

            # Convert calculated minutes back into timedelta objects for consistent
            # HH:MM:SS (or HH:MM) formatting.
            # For break_time_left, use max(0, ...) to avoid displaying negative time.
            break_time_spent_td = datetime.timedelta(minutes=break_time_spent_minutes)
            break_time_left_td = datetime.timedelta(minutes=max(0, break_time_left_minutes))
            effective_work_time_td = datetime.timedelta(minutes=effective_work_minutes)
            
            # Format timedelta objects for display, stripping microseconds
            break_time_spent_display = str(break_time_spent_td).split('.')[0]
            break_time_left_display = str(break_time_left_td).split('.')[0]
            effective_work_time_display = str(effective_work_time_td).split('.')[0]

            # Determine the status message based on compliance with work rules
            if effective_work_minutes >= REQUIRED_WORK_MINUTES:
                # If effective work time meets or exceeds the requirement
                status_message = "You can meet your work time requirement."
                status_color = "text-green-600" # Positive status

                if break_time_left_minutes < 0:
                    # If designated break time was exceeded
                    exceeded_minutes = abs(break_time_left_minutes)
                    exceeded_td = datetime.timedelta(minutes=exceeded_minutes)
                    status_message += (
                        f" However, you have exceeded your designated break by "
                        f"{str(exceeded_td).split('.')[0]}."
                    )
                    status_color = "text-orange-600" # Warning, but not critical failure
                elif break_time_left_minutes > 0:
                    # If there's still break time remaining
                    status_message += f" You have {break_time_left_display} break time remaining."
                    status_color = "text-green-600"
                else: # break_time_left_minutes == 0
                    # If exactly all designated break time has been used
                    status_message += " You have used all your designated break time."
                    status_color = "text-green-600"
            else:
                # If effective work time is less than the required work time
                status_message = (
                    f"Warning: Your effective work time ({effective_work_time_display}) "
                    f"is less than the required {REQUIRED_WORK_MINUTES // 60}h "
                    f"{REQUIRED_WORK_MINUTES % 60}m. This is due to the break "
                    f"duration you've taken (or plan to take)."
                )
                status_color = "text-red-600" # Critical warning/failure

    except ValueError:
        # Handles errors if time strings are not in the expected HH:MM format
        status_message = "Invalid time format. Please use HH:MM for both arrival and break time spent."
        status_color = "text-red-600"
    except Exception as e:
        # Catches any other unforeseen errors during processing
        status_message = f"An unexpected error occurred: {e}"
        status_color = "text-red-600"

    # Render the index.html template, passing all calculated and status variables
    return render_template(
        'index.html',
        arrival_time_str=arrival_time_str,
        break_time_spent_str=break_time_spent_str,
        departure_time=required_departure_time_display,
        break_time_spent=break_time_spent_display,
        break_time_left=break_time_left_display,
        effective_work_time=effective_work_time_display,
        status_message=status_message,
        status_color=status_color
    )

if __name__ == '__main__':
    # Run the Flask application in debug mode.
    # 'debug=True' allows for automatic code reloading and a debugger in the browser.
    app.run(debug=True)
