"""# Setup Instructions

## Prerequisites
- Python 3.8 or higher installed on your PC
- Internet connection (for installing packages)

## Steps to Setup

1. Extract the zip folder to a location on your PC (e.g., `C:\projects\hms`)

2. Open Command Prompt or PowerShell in the extracted folder

3. Create a virtual environment:
   ```
   python -m venv venv
   ```

4. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

5. Install required packages:
   ```
   pip install -r requirements.txt
   ```

6. Run the application:
   ```
   streamlit run app.py
   ```

7. The application will open in your web browser at `http://localhost:8501`

## Default Login Credentials

- **Admin**: username: `admin`, password: `admin123`
- **Doctor**: username: `doctor`, password: `doctor123`
- **Receptionist**: username: `reception`, password: `reception123`

## Notes

- The database will be created automatically on first run in the `data` folder
- Default users will be created automatically
- If you encounter any errors, make sure Python 3.8+ is installed and all packages are installed correctly

"""