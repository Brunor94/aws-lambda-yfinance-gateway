#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import zipfile

def check_python_version():
    """
    Verify that Python 3.9 is being used
    """
    version_info = sys.version_info
    if version_info.major != 3 or version_info.minor != 9:
        print(f"\nWARNING: This script is designed for Python 3.9.\nCurrent Python version: {sys.version}")
        print("The deployment package may not be compatible with AWS Lambda Python 3.9 runtime.")
        response = input("Do you want to continue anyway? (y/n): ")
        return response.lower() == 'y'
    print(f"Python version check passed: {sys.version}")
    return True

def create_deployment_package():
    """
    Creates a deployment package for AWS Lambda
    """
    print("Creating AWS Lambda deployment package...")
    
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    package_dir = os.path.join(base_dir, "package")
    deployment_zip = os.path.join(base_dir, "deployment.zip")
    
    # Clean up any existing package directory or zip file
    if os.path.exists(package_dir):
        print(f"Removing existing package directory: {package_dir}")
        shutil.rmtree(package_dir)
    
    if os.path.exists(deployment_zip):
        print(f"Removing existing deployment zip: {deployment_zip}")
        os.remove(deployment_zip)
    
    # Check if there are any requirements
    requirements_file = os.path.join(base_dir, "requirements.txt")
    has_requirements = os.path.exists(requirements_file) and os.path.getsize(requirements_file) > 0
    
    if has_requirements:
        # Create a directory for the packages
        os.makedirs(package_dir)
        
        # Install dependencies to the package directory
        print("Installing dependencies to package directory...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                  "-r", requirements_file, "-t", package_dir])
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            return False
        
        # Create the deployment package with dependencies
        print("Creating deployment package with dependencies...")
        with zipfile.ZipFile(deployment_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the package directory
            for root, _, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arcname)
            
            # Add the lambda function
            lambda_file = os.path.join(base_dir, "lambda_function.py")
            zipf.write(lambda_file, os.path.basename(lambda_file))
    else:
        # Create a simple deployment package with just the lambda function
        print("Creating simple deployment package...")
        with zipfile.ZipFile(deployment_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            lambda_file = os.path.join(base_dir, "lambda_function.py")
            zipf.write(lambda_file, os.path.basename(lambda_file))
    
    # Verify the deployment package was created
    if os.path.exists(deployment_zip):
        size_mb = os.path.getsize(deployment_zip) / (1024 * 1024)
        print(f"Deployment package created successfully: {deployment_zip} ({size_mb:.2f} MB)")
        return True
    else:
        print("Failed to create deployment package")
        return False

if __name__ == "__main__":
    # Check Python version before proceeding
    if check_python_version():
        create_deployment_package()
    else:
        print("Deployment package creation aborted due to Python version mismatch.")
        print("Please use Python 3.9 for compatibility with AWS Lambda runtime.")
