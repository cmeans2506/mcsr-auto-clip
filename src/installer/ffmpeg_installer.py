import sys
import zipfile
import requests
import winreg
from pathlib import Path
from tqdm import tqdm
import ctypes


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


class FFmpegInstaller:
    def __init__(self):
        self.download_url = (
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
            "ffmpeg-master-latest-win64-gpl.zip"
        )

        self.install_dir = Path.home() / "ffmpeg"
        self.zip_path = self.install_dir / "ffmpeg.zip"
        
    def create_install_directory(self):
        print(f"creating the install directory: {self.install_dir}")
        self.install_dir.mkdir(parents=True, exist_ok=True)
        
    def download_ffmpeg(self):
        print(f"\ndownloading FFmpeg...")
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
    
    def extract_ffmpeg(self):
        print(f"\nextracting FFmpeg...")
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                members = zip_ref.namelist()
                
                with tqdm(total=len(members), desc="extraction progress") as pbar:
                    for member in members:
                        zip_ref.extract(member, self.install_dir)
                        pbar.update(1)
            
            self.zip_path.unlink()
            print(f"extraction completed: {self.install_dir}")
            
            bin_dirs = list(self.install_dir.glob("*/bin"))
            self.bin_path = bin_dirs[0]
            print(f"FFmpeg executable: {self.bin_path}")
                
        except Exception as e:
            print(f"extraction failed: {e}")
            raise
    
    def add_to_environment_variable(self):
        print(f"\nadding to environment variable...")
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Environment',
                0,
                winreg.KEY_READ | winreg.KEY_WRITE
            )
            
            try:
                current_path, _ = winreg.QueryValueEx(key, 'Path')
            except FileNotFoundError:
                current_path = ''
            
            bin_path_str = str(self.bin_path)
            paths = [p.strip() for p in current_path.split(';') if p.strip()]
            
            if bin_path_str in paths:
                print(f"{bin_path_str} is in the environment variable")
            else:
                new_path = ';'.join(paths + [bin_path_str])
                winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
                print(f"{bin_path_str} has been added to the environment variable")
            
            winreg.CloseKey(key)
            
        except Exception as e:
            print(f"failed to add to environment variable: {e}")
            print(f"please add this to environment variable `PATH` manually: {self.bin_path}")
            raise
    
   
    def install(self):      
        self.create_install_directory()
        
        self.download_ffmpeg()
        
        self.extract_ffmpeg()
        
        self.add_to_environment_variable()

def main():   
    installer = FFmpegInstaller()
    try:
        installer.install()
    except KeyboardInterrupt:
        print("\n\ninstallation has been canceled.")
    except Exception as e:
        print(f"\nException during installation: {e}")
        import traceback
        traceback.print_exc()
    else:
        print("ffmpeg has been successfully installed!")

if __name__ == "__main__":
    print("=" * 40)
    print("FFmpeg Installer")
    print("=" * 40)

    if not is_admin():
        input("\nNot running as admin, press enter to rerun as admin!")
        # rerun as admin
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    else:   
        print("running as admin...")
    
    main()
    input("press enter to exit the installer!")