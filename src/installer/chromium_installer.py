import zipfile
import requests
from pathlib import Path
from tqdm import tqdm
import ctypes
import json


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


class ChromiumInstaller:
    def __init__(self):
        self.download_url = (
            "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/"
            "Win_x64%2F1250504%2Fchrome-win.zip?generation=1705968802991678&alt=media"
        )

        self.install_dir = Path.home() / "chromium"
        self.zip_path = self.install_dir / "chromium.zip"

    def create_install_directory(self):
        print(f"creating the install directory: {self.install_dir}")
        self.install_dir.mkdir(parents=True, exist_ok=True)

    def download_chromium(self):
        print(f"\ndownloading chromium...")
        print(f"download url: {self.download_url}")

        try:
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(self.zip_path, 'wb') as f, tqdm(
                    desc="download progress",
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

            print(f"download completed: {self.zip_path}")

        except requests.exceptions.RequestException as e:
            print(f"download failed, please check your network connection: {e}")
            raise

    def extract_chromium(self):
        print(f"\nextracting chromium...")

        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                members = zip_ref.namelist()

                with tqdm(total=len(members), desc="extraction progress") as pbar:
                    for member in members:
                        zip_ref.extract(member, self.install_dir)
                        pbar.update(1)

            self.zip_path.unlink()
            print(f"extraction completed: {self.install_dir}")

            exe_files = list(self.install_dir.glob("**/chrome.exe"))
            if exe_files:
                self.bin_path = exe_files[0]
                print(f"chromium 可执行文件位置: {self.bin_path}")

        except Exception as e:
            print(f"extraction failed: {e}")
            raise

    # def change_config_file(self):
    #     print(f"\nchanging the config file...")
    #     config_file_path = Path(__file__).parent.parent.parent / 'config' / 'config.json'
    #     with open(config_file_path, 'r', encoding='utf-8') as config_file:
    #         config_content = json.load(config_file)
    #     config_content['browser_executable'] = self.bin_path.as_posix()
    #     with open(config_file_path, 'w', encoding='utf-8') as config_file:
    #         json.dump(config_content, config_file, indent=2, ensure_ascii=False)


    def install(self):
        self.create_install_directory()

        self.download_chromium()

        self.extract_chromium()

        # self.change_config_file()


def main():
    installer = ChromiumInstaller()
    try:
        installer.install()
    except KeyboardInterrupt:
        print("\n\ninstallation has been canceled.")
    except Exception as e:
        print(f"\nException during installation: {e}")
        import traceback
        traceback.print_exc()
    else:
        print("chromium has been successfully installed!")


if __name__ == "__main__":
    print("=" * 40)
    print("Chromium Installer")
    print("=" * 40)

    main()
    input("press enter to exit the installer!")