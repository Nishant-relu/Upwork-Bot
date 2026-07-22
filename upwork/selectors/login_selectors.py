class UpworkLoginSelectors:
    # Login Form Fields
    USERNAME_INPUT = "#login_username"
    PASSWORD_INPUT = "#login_password"
    SECURITY_ANSWER_INPUT = "#login_answer"

    # Buttons
    CONTINUE_TO_PASSWORD_BUTTON = "#login_password_continue"
    LOGIN_SUBMIT_BUTTON = "#login_control_continue"
    LOGIN_NAV_LINK = 'a[data-qa="login"]'

    # Checkbox
    REMEMBER_ME_CHECKBOX = 'span[data-test="checkbox-input"]'

    # Captcha
    CAPTCHA_RESPONSE_INPUT = 'input[name="cf-turnstile-response"]'

    # Post-login Element (used for login success detection)
    USER_MENU_LIST_ITEM = 'li[data-cy="user-menu"]'
    USER_PROFILE = 'section[data-test="my-profile"]'
    # New sidebar (redesigned UI) — visible on all logged-in pages, not obscured by FTE tour popovers
    SIDEBAR_PROFILE = '[data-test="profile_and_account"]'
