::ANSI
@echo off

:: ����Ƿ��Թ���Ա�������
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo �����������ԱȨ��...
    goto UACPrompt
) else (
    goto gotAdmin
)

:UACPrompt
:: ����һ����ʱ VBScript �ļ�������Ȩ��
echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
"%temp%\getadmin.vbs"
del /f /q "%temp%\getadmin.vbs"
exit /B

:gotAdmin
echo �ѳɹ���ù���ԱȨ�ޡ�


:: �ṩ����ѡ��
echo ��ѡ��Ҫִ�еĲ�����
echo 1. �ر�Windows Defender
echo 2. ȡ���ر�Windows Defender
set /p choice=������ѡ�� (1 �� 2): 

:: �ж�ѡ��
if '%choice%' EQU '1' goto disable Defender
if '%choice%' EQU '2' goto Undisable Defender
echo ��Ч��ѡ����������нű���
pause
exit /B

:: �ر�Windows Defender
:disable Defender
echo ���ڹر�Windows Defender...
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows Defender" /v "DisableAntiSpyware" /t REG_DWORD /d 1 /f
echo Windows Defender�Ѿ��ر�
goto reboot

:: ȡ���ر�Windows Defender
:Undisable Defender
echo ����ȡ���ر�Windows Defender...
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows Defender" /v "DisableAntiSpyware" /t REG_DWORD /d 0 /f
goto reboot

:: ���������
:reboot
echo ����Ҫ�����������������ʹ������Ч
echo 1. �����������������
echo 2. �Ժ��������������
set /p choice=������ѡ�� (1 �� 2): 

:: �ж�ѡ��
if '%choice%' EQU '1' goto restart
if '%choice%' EQU '2' goto exit
echo ��Ч��ѡ����������нű���
pause
exit /B

:: �������������
:restart
echo ���������30�����������...
shutdown /r /t 30 /c "Windows Defender�������Ѹ��£�30s���������������"
exit /B

:: �˳��ű�
:exit
exit /B
