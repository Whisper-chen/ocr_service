'''
Copyright (c) 2024 Qualcomm Innovation Center, Inc. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause-Clear
'''

import asyncio
import time

import cv2
import pytesseract
import rclpy
from cv_bridge import CvBridge
from ocr_msg.srv import OcrRequest
from rclpy.experimental import AsyncNode
from sensor_msgs.msg import Image
from std_msgs.msg import String


DEFAULT_MAX_CONCURRENT_OCR = 2
DEFAULT_TOPIC_IDLE_TIMEOUT_SEC = 30.0
DEFAULT_CLEANUP_PERIOD_SEC = 5.0
DEFAULT_DROP_FRAMES_WHEN_BUSY = True


class OcrService(AsyncNode):
    def __init__(self):
        super().__init__('ocr_service')

        self.declare_parameter('max_concurrent_ocr', DEFAULT_MAX_CONCURRENT_OCR)
        self.declare_parameter(
            'topic_idle_timeout_sec',
            DEFAULT_TOPIC_IDLE_TIMEOUT_SEC,
        )
        self.declare_parameter('cleanup_period_sec', DEFAULT_CLEANUP_PERIOD_SEC)
        self.declare_parameter(
            'drop_frames_when_busy',
            DEFAULT_DROP_FRAMES_WHEN_BUSY,
        )

        max_concurrent_ocr = self.get_parameter(
            'max_concurrent_ocr'
        ).get_parameter_value().integer_value
        self.topic_idle_timeout_sec = self.get_parameter(
            'topic_idle_timeout_sec'
        ).get_parameter_value().double_value
        cleanup_period_sec = self.get_parameter(
            'cleanup_period_sec'
        ).get_parameter_value().double_value
        self.drop_frames_when_busy = self.get_parameter(
            'drop_frames_when_busy'
        ).get_parameter_value().bool_value

        self.bridge = CvBridge()
        self.processors = {}
        self.ocr_concurrency = asyncio.Semaphore(max(1, max_concurrent_ocr))

        self.srv = self.create_service(
            OcrRequest,
            'OcrRequest',
            self.handle_ocr_request,
        )
        self.cleanup_timer = self.create_timer(
            max(1.0, cleanup_period_sec),
            self.cleanup_idle_topics,
        )

        self.get_logger().info(
            'OCR service started: '
            f'max_concurrent_ocr={max(1, max_concurrent_ocr)}, '
            f'topic_idle_timeout_sec={self.topic_idle_timeout_sec}, '
            f'drop_frames_when_busy={self.drop_frames_when_busy}'
        )

    async def handle_ocr_request(self, request, response):
        image_topic = request.image_node.strip()

        if not image_topic:
            response.success = False
            response.ocr_node = ''
            self.get_logger().error('Empty image topic in OCR request')
            return response

        if image_topic not in self.processors:
            self.add_image_topic(image_topic)
        else:
            self.processors[image_topic]['last_request_time'] = time.monotonic()

        response.success = True
        response.ocr_node = self.processors[image_topic]['output_topic']
        self.get_logger().info(
            f'OCR topic active: {image_topic} -> {response.ocr_node}'
        )
        return response

    def add_image_topic(self, image_topic):
        output_topic = self.make_output_topic(image_topic)
        publisher = self.create_publisher(String, output_topic, 10)
        subscription = self.create_subscription(
            Image,
            image_topic,
            self.make_image_callback(image_topic),
            10,
        )

        now = time.monotonic()
        self.processors[image_topic] = {
            'subscription': subscription,
            'publisher': publisher,
            'output_topic': output_topic,
            'active_count': 0,
            'last_message_time': now,
            'last_request_time': now,
            'received_count': 0,
            'published_count': 0,
            'dropped_count': 0,
        }
        self.get_logger().info(f'Registered OCR topic: {image_topic}')

    def make_image_callback(self, image_topic):
        async def callback(msg):
            await self.process_image(image_topic, msg)

        return callback

    async def process_image(self, image_topic, msg):
        processor = self.processors.get(image_topic)
        if processor is None:
            return

        processor['last_message_time'] = time.monotonic()
        processor['received_count'] += 1

        if self.drop_frames_when_busy and processor['active_count'] > 0:
            processor['dropped_count'] += 1
            self.get_logger().debug(f'Skip busy OCR topic frame: {image_topic}')
            return

        processor['active_count'] += 1
        try:
            async with self.ocr_concurrency:
                text = await asyncio.to_thread(self.run_ocr, msg)

            current_processor = self.processors.get(image_topic)
            if current_processor is None:
                return

            result = String()
            result.data = text
            current_processor['publisher'].publish(result)
            current_processor['published_count'] += 1
            self.get_logger().info(
                'Published OCR result: '
                f'{image_topic} -> {current_processor["output_topic"]}'
            )
        except Exception as error:
            self.get_logger().error(f'OCR failed for topic {image_topic}: {error}')
        finally:
            current_processor = self.processors.get(image_topic)
            if current_processor is not None:
                current_processor['active_count'] -= 1

    async def cleanup_idle_topics(self):
        if self.topic_idle_timeout_sec <= 0:
            return

        now = time.monotonic()
        idle_topics = []
        for image_topic, processor in self.processors.items():
            if processor['active_count'] > 0:
                continue
            if now - processor['last_message_time'] >= self.topic_idle_timeout_sec:
                idle_topics.append(image_topic)

        for image_topic in idle_topics:
            self.remove_image_topic(image_topic)

    def remove_image_topic(self, image_topic):
        processor = self.processors.pop(image_topic, None)
        if processor is None:
            return

        self.destroy_subscription(processor['subscription'])
        self.destroy_publisher(processor['publisher'])
        self.get_logger().info(
            'Removed idle OCR topic: '
            f'{image_topic} -> {processor["output_topic"]}, '
            f'received={processor["received_count"]}, '
            f'published={processor["published_count"]}, '
            f'dropped={processor["dropped_count"]}'
        )

    def run_ocr(self, msg):
        rgb = self.bridge.imgmsg_to_cv2(msg, 'rgb8')
        img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        return pytesseract.image_to_string(img)

    def make_output_topic(self, image_topic):
        return f'{image_topic.rstrip("/")}_ocr'


async def async_main():
    with rclpy.init():
        node = OcrService()
        await node.run()


def main():
    asyncio.run(async_main())


if __name__ == '__main__':
    main()
