import subprocess
import os

def run_git_command(command):
    """通用 Git 命令执行器"""
    try:
        # 确保在项目根目录执行（即 src 的上一级）
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        result = subprocess.run(
            command, 
            cwd=root_dir, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8' # 解决 Windows 下的编码问题
        )
        if result.returncode == 0:
            print(f"✅ [Git] 执行成功: {' '.join(command) if isinstance(command, list) else command}")
            return True
        else:
            print(f"❌ [Git] 错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️ [Git] 异常: {e}")
        return False

def push_to_github():
    """执行完整的推送流程"""
    print("🚀 [GitHub] 启动同步流程...")

    # 1. 预处理：解决你之前遇到的分支分歧配置问题
    run_git_command("git config pull.rebase false")

    # 2. 添加更改 (包括 index.html 和新的 data/json)
    run_git_command("git add .")

    # 3. 提交
    commit_msg = f"Auto-update: Macro Data {os.path.basename(os.getcwd())}"
    run_git_command(f'git commit -m "{commit_msg}"')

    # 4. 推送
    # 注意：这里假设你已经配置好了 SSH 或凭据助手，不再需要手动输密码
    success = run_git_command("git push origin main")
    
    if success:
        print("🎉 [成功] 网页已更新并推送到 GitHub Pages！")
    else:
        print("❌ [失败] 推送未成功，请检查网络或 Token 权限。")

if __name__ == "__main__":
    push_to_github()