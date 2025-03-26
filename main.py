from pyicloud import PyiCloudService
import sys, os
from tqdm import tqdm

def create_client(user: str, password: str):
    api = PyiCloudService(user, password)
    if api.requires_2fa:
        print("Two-factor authentication required.")
        code = input("Enter the code you received of one of your approved devices: ")
        result = api.validate_2fa_code(code)
        print("Code validation result: %s" % result)

        if not result:
            print("Failed to verify security code")
            sys.exit(1)

        if not api.is_trusted_session:
            print("Session is not trusted. Requesting trust...")
            result = api.trust_session()
            print("Session trust result %s" % result)

            if not result:
                print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")
    elif api.requires_2sa:
        import click
        print("Two-step authentication required. Your trusted devices are:")

        devices = api.trusted_devices
        for i, device in enumerate(devices):
            print(
                "  %s: %s" % (i, device.get('deviceName',
                "SMS to %s" % device.get('phoneNumber')))
            )

        device = click.prompt('Which device would you like to use?', default=0)
        device = devices[device]
        if not api.send_verification_code(device):
            print("Failed to send verification code")
            sys.exit(1)

        code = click.prompt('Please enter validation code')
        if not api.validate_verification_code(device, code):
            print("Failed to verify verification code")
            sys.exit(1)
    return api

def download_images(client, output_directory='icloud_downloads'):

    os.makedirs(output_directory, exist_ok=True)

    # Get all photos
    photos = client.photos.all
    total_photos = len(photos)

    print(f"Total Photos Found: {total_photos}")

    for index, photo in enumerate(tqdm(photos, desc="Downloading Photos", unit="photo"), 1):
        try:
            # Generate unique filename to prevent overwriting
            filename = os.path.join(
                output_directory, 
                f"{index}_{photo.filename}"
            )
            
            # Skip if file already exists
            if os.path.exists(filename):
                continue
            
            # Download photo
            download = photo.download()
            
            # Write to file
            with open(filename, 'wb') as opened_file:
                opened_file.write(download.raw.read())
            
        except Exception as download_error:
            print(f"Error downloading photo {index}: {download_error}")
            continue
        
    print("Photo download complete!")


def download_contacts(client):
    for c in client.contacts.all():
        print(c.get('firstName'), c.get('phones'))

def find_my_phone(client):
    return client.iphone.status()

if __name__ == '__main__':
    email = os.getenv("USEREMAIL")
    password = os.getenv("USERPASSWORD")
    download_dir = os.getenv("DOWNLOADDIR")
    
    icloud_client = create_client(email, password)
    # print(find_my_phone(icloud_client))
    # download_contacts(icloud_client)
    download_images(icloud_client, download_dir)
    