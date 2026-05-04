```python
import datetime

def log_safety_incident(incident_description):
    """
    Logs a safety incident with a timestamp.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] INCIDENT: {incident_description}\n"
    
    try:
        with open("safety_log.txt", "a") as f:
            f.write(log_entry)
        print(f"Incident logged successfully: {incident_description}")
    except IOError as e:
        print(f"Error writing to log file: {e}")

if __name__ == "__main__":
    print("Welcome to the Safety Sentinel Log. Report recurring frustrations.")
    print("Type 'exit' to quit.")

    while True:
        user_input = input("Describe the safety incident: ")
        if user_input.lower() == 'exit':
            break
        elif user_input:
            log_safety_incident(user_input)
        else:
            print("Please provide a description.")
    
    print("Exiting Safety Sentinel. Stay vigilant!")
```