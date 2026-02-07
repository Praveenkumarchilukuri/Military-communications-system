# Military Communications Application

This is a secure messaging application with a military hierarchy and hybrid encryption (Vigenere + Polybius).

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Database Setup:**
    - Ensure you have a MySQL server running on `localhost:3306`.
    - Create the database and tables using the `db.sql` file:
      ```bash
      mysql -u root -p < db.sql
      ```
    - Update `military_comms/settings.py` with your MySQL credentials if they differ from `root`/`root`.

3.  **Run the Server:**
    ```bash
    python manage.py runserver
    ```

4.  **Access the Application:**
    - Open your browser and go to `http://127.0.0.1:8000/`.

## Features

- **Hierarchy:**
    - Admin approves Major General.
    - Major General approves Brigadier.
    - Brigadier approves Colonel.
- **Security:**
    - Messages are encrypted using a Hybrid Cipher (Vigenere + Polybius).
    - Decryption keys are emailed to the recipient upon reading the message.
    - Keys are NOT stored with the message in a readable format (they are stored in the DB, but separated).

## Usage

1.  **Signup:** Create accounts for different roles.
2.  **Approval:** Log in as a superior officer to approve pending accounts.
3.  **Messaging:** Send encrypted messages to other users.
4.  **Reading:** Click on a message to receive the decryption key via email, then enter it to read the message.
