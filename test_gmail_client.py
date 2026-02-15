import os

# Other existing import statements


def exists_side_effect(path):
    return path == 'credentials.json'

# Other existing code...

def test_authenticate_with_oauth_flow():
    # Previous lines of the method
    # Mock the os.path.exists function
    mock_exists = mock.patch('os.path.exists').start()
    mock_exists.side_effect = exists_side_effect
    
    # Lines 32-42 unchanged

# ... remaining code in the file unchanged
