# Use the official AWS Lambda Python 3.9 base image
FROM public.ecr.aws/lambda/python:3.9

# Copy the requirements file into the container
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the Python dependencies
RUN pip install -r requirements.txt --target ${LAMBDA_TASK_ROOT}

# Copy your Lambda function code into the container
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (already default for this base image, but good to be explicit)
CMD [ "lambda_function.lambda_handler" ]