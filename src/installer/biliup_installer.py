import sys
import zipfile
import requests
import winreg
from pathlib import Path
from tqdm import tqdm
import ctypes


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


class BiliupInstaller:
    def __init__(self):
        self.github_api_url = "https://api.github.com/repos/biliup/biliup/releases/latest"
        self.install_dir = Path.home() / "biliup"
        self.zip_path = self.install_dir / "biliup.zip"
        self.download_url = None
        
    def get_latest_release_url(self):
        print(f"\n获取最新版本信息...")
        
        try:
            response = requests.get(self.github_api_url, timeout=30)
            response.raise_for_status()
            
            release_data = response.json()
            version = release_data['tag_name']
            
            # 在 assets 中查找 biliupR-*-x86_64-windows.zip
            for asset in release_data['assets']:
                name = asset['name']
                if name.startswith('biliupR-') and name.endswith('x86_64-windows.zip'):
                    self.download_url = asset['browser_download_url']
                    print(f"找到最新版本: {version}")
                    print(f"文件名: {name}")
                    return
            
            raise Exception("未找到 Windows x86_64 版本的下载文件")
            
        except requests.exceptions.RequestException as e:
            print(f"获取版本信息失败，请检查网络连接: {e}")
            raise
        except KeyError as e:
            print(f"解析版本信息失败: {e}")
            raise
        
    def create_install_directory(self):
        print(f"\n创建安装目录: {self.install_dir}")
        self.install_dir.mkdir(parents=True, exist_ok=True)
        
    def download_biliup(self):
        print(f"\n下载 biliup...")
        print(f"下载地址: {self.download_url}")
        
        try:
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(self.zip_path, 'wb') as f, tqdm(
                desc="下载进度",
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            print(f"下载完成: {self.zip_path}")
            
        except requests.exceptions.RequestException as e:
            print(f"下载失败，请检查网络连接: {e}")
            raise
    
    def extract_biliup(self):
        print(f"\n解压 biliup...")
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                members = zip_ref.namelist()
                
                with tqdm(total=len(members), desc="解压进度") as pbar:
                    for member in members:
                        zip_ref.extract(member, self.install_dir)
                        pbar.update(1)
            
            self.zip_path.unlink()
            print(f"解压完成: {self.install_dir}")
            
            # 查找 biliup 可执行文件
            exe_files = list(self.install_dir.glob("**/biliup.exe"))
            if exe_files:
                self.bin_path = exe_files[0].parent
                print(f"biliup 可执行文件位置: {self.bin_path}")
                
        except Exception as e:
            print(f"解压失败: {e}")
            raise
    
    def add_to_environment_variable(self):
        print(f"\n添加到环境变量...")
        
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
                print(f"{bin_path_str} 已存在于环境变量中")
            else:
                new_path = ';'.join(paths + [bin_path_str])
                winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
                print(f"{bin_path_str} 已添加到环境变量")
            
            winreg.CloseKey(key)
            
        except Exception as e:
            print(f"添加环境变量失败: {e}")
            print(f"请手动将此路径添加到环境变量 PATH 中: {self.bin_path}")
            raise
    
   
    def install(self):      
        self.get_latest_release_url()
        
        self.create_install_directory()
        
        self.download_biliup()
        
        self.extract_biliup()
        
        self.add_to_environment_variable()


def main():   
    installer = BiliupInstaller()
    try:
        installer.install()
        print("\nbiliup 已成功安装!")
    except KeyboardInterrupt:
        print("\n\n安装已取消。")
    except Exception as e:
        print(f"\n安装过程中出现异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 40)
    print("biliup 安装程序")
    print("=" * 40)

    if not is_admin():
        input("\n未以管理员身份运行，按回车键以管理员身份重新运行!")
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    else:   
        print("正在以管理员身份运行...")
    
    main()
    input("\n按回车键退出安装程序!")