from setuptools import setup, find_packages

setup(
    name="examtool",
    licence="MIT",
    packages=find_packages(include=["apps"]),
    entry_points={
        "console_scripts": [
            "deploy=scripts.upload:upload_exam",
            "compile=scripts.compile_all:compile_all",
            "check_dupes=scripts.check_dupes:check_dupes",
            "download=scripts.download_all:download_all",
            "logs=scripts.last_submission:get_last_submission",
            "upload=scripts.gradescope_upload:upload_folder",
            "send=scripts.send_emails:send_emails",
        ]
    }
)
