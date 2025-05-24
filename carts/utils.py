# for helper functions

def get_session_key(request):
    session_key = request.session.session_key  # Get the session_key ID from the session
    if not session_key:
        session_key = request.session.create()  # Create a new session key if it doesn't exist
    return session_key
    """
    if not request.session.session_key:
            request.session.create()
        return request.session.session_key
    """
