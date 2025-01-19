::ANSI
@echo off

:: 检查是否以管理员身份运行
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 正在请求管理员权限...
    goto UACPrompt
) else (
    goto gotAdmin
)

:UACPrompt
:: 创建一个临时 VBScript 文件以提升权限
echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
"%temp%\getadmin.vbs"
del /f /q "%temp%\getadmin.vbs"
exit /B

:gotAdmin
echo 已成功获得管理员权限。


:: 提供功能选择
echo 请选择要执行的操作：
echo 1. 关闭Windows Defender
echo 2. 取消关闭Windows Defender
set /p choice=请输入选项 (1 或 2): 

:: 判定选项
if '%choice%' EQU '1' goto disable Defender
if '%choice%' EQU '2' goto Undisable Defender
echo 无效的选项，请重新运行脚本。
pause
exit /B

:: 关闭Windows Defender
:disable Defender
echo 正在关闭Windows Defender...
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows Defender" /v "DisableAntiSpyware" /t REG_DWORD /d 1 /f
echo Windows Defender已经关闭
goto reboot

:: 取消关闭Windows Defender
:Undisable Defender
echo 正在取消关闭Windows Defender...
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows Defender" /v "DisableAntiSpyware" /t REG_DWORD /d 0 /f
goto reboot

:: 重启计算机
:reboot
echo 您需要重新启动计算机才能使设置生效
echo 1. 现在重新启动计算机
echo 2. 稍后重新启动计算机
set /p choice=请输入选项 (1 或 2): 

:: 判定选项
if '%choice%' EQU '1' goto restart
if '%choice%' EQU '2' goto exit
echo 无效的选项，请重新运行脚本。
pause
exit /B

:: 重新启动计算机
:restart
echo 计算机将在30秒后重新启动...
shutdown /r /t 30 /c "Windows Defender的设置已更新，30s后重新启动计算机"
exit /B

:: 退出脚本
:exit
exit /B
