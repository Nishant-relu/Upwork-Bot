from .env import get_env

def get_credentials(account_name: str) -> tuple[str, str, str]:
    """gets login credentials from env based on name of user."""
    
    email = get_env(f"{account_name.upper()}_EMAIL")
    password = get_env(f"{account_name.upper()}_PASSWORD")
    sec_answer = get_env(f"{account_name.upper()}_SECRET_ANSWER")
    if not all([email, password, sec_answer]):
        raise ValueError("Missing credentials for account.")
    return email, password, sec_answer


if __name__ == '__main__':
    print(get_credentials('muktesh'))
