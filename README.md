# ocr_service User Guide
Here comes the User Guide for OCR Service, it will contain some detail show as below.

- the service definition and it's output and input.
- how to install debian package & dependencies from Ubuntu PPA
- how to run this project.
- how to build this project.


## Service
### Client

| input                                 | output                                                        |
| ------------------------------------- | ------------------------------------------------------------- |
| Topic name : image topic name(String) | Topic name : OCR result (String) <br>OCR request status: Bool |

### Server and Process Node：

| Input                     | Output                 |
| ------------------------- | ---------------------- |
| Topic : sensor_msgs/Image | Topic : Std_msg/String |

### Test Node:

| Input                     | Output                                              |
| ------------------------- | --------------------------------------------------- |
| String : image topic name <br> String : picture path |  Topic : sensor_msgs/Image |
## Service msg

### ocr_service::ocr_msg::OcrRequest

```
string image_topic_name
---
string ocr_topic_name
bool success
```
## installation
Add Qualcomm IOT PPA for Ubuntu
```
sudo add-apt-repository ppa:ubuntu-qcom-iot/qcom-ppa
sudo add-apt-repository ppa:ubuntu-qcom-iot/qirp
sudo apt update

```
Install Debian package
```
sudo apt install ros-jazzy-ocr-service 
```
Install python dependency
```
pip3 install pytesseract
```

## Usage
Run ocr_service and ocr_testnode on device:

```bash
Terminal 1: launch ocr_server
export HOME=/home
source /opt/ros/jazzy/setup.bash
ros2 run ocr_service ocr_server

terminal 2: lanunch ocr_testnode
export HOME=/home
source /opt/ros/jazzy/setup.sh
ros2 run ocr_service ocr_testnode --topic <image_topic> --picture <image_path>

terminal 3:launch ocr_client
export HOME=/home
source /opt/ros/jazzy/setup.sh
ros2 run ocr_service ocr_client  <image_topic>
```

## Build from source

### Dependencies
install dependencies:
```
apt install ros-jazzy-example-interfaces, ros-jazzy-ocr-msg, python3-setuptools
```
Build OCR_Service:
```bash

git clone https://github.com/qualcomm-qrb-ros/ocr_service.git
colcon build 

```

## License

This is licensed under the BSD 3-Clause-Clear “New” or “Revised” License.
