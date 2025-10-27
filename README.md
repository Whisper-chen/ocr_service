# ocr_service User Guide
Here comes the User Guide for OCR Service, it will contain some detail show as below.

- the service definition and it's output and input.
- how to build this project.
- how to push binary to device.
- how to run this project.

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

Build OCR_Service:
```bash

cd <QIRP_SDK>
git clone
colcon build --merge-install --cmake-args ${CMAKE_ARGS}

```

## Push
Push OCR_msg OCR_Service and test picture to device:

```bash
cd install
tar -zcvf ocr_service.tar.gz include/ lib/ share/
ssh root@[ip-addr]
(ssh) mount -o remount rw /
scp ocr_service.tar.gz root@[ip-addr]:/opt
ssh ssh root@[ip-addr]
(ssh) tar --no-overwrite-dir --no-same-owner -zxf /opt/ocr_service.tar.gz -C /usr/

scp  <your pciture> root@[ip-addr]:/opt
```

## RUN
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

## License

This is licensed under the BSD 3-Clause-Clear “New” or “Revised” License.
