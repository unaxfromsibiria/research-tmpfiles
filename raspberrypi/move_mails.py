#!/usr/bin/env python3

import os
import picamera
import smtplib
import signal
import time
import tempfile
import uuid
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
from os.path import join as path_join

import RPi.GPIO as gpio


load_dotenv(find_dotenv())
# pin of interior lighting for photographing
LIGHT_PIN = int(
    os.environ.get("LIGHT_PIN") or 7)
# pin of HCSR501
SENSOR_PIN = int(
    os.environ.get("SENSOR_PIN") or 24)
SEND_TIME_INTERVAL_LIMIT = int(
    os.environ.get("SEND_TIME_INTERVAL_LIMIT") or 30)
LIGHT_ON_TIME_LIMIT = 3600 // 2
TMP_DIR = os.environ.get("TMP_DIR") or tempfile.mkdtemp()
IMAGE_SIZE = os.environ.get("IMAGE_SIZE") or ""
PHOTO_SERIES = int(os.environ.get("PHOTO_SERIES") or 3)


class FileList(list):
    """List for files (photo files).
    """
    def clear(self):
        if self:
            for file_path in self:
                try:
                    os.remove(file_path)
                except Exception as err:
                    manager.log(err, "file remove")
        super().clear()


class SytemManager:
    """Manager of devices and processing.
    """
    state = None
    inst_id = log_file_name = None
    _camera_conf = None

    def __init__(self):
        self.inst_id = code = uuid.uuid4().hex[:4]
        self.state = {
            "active": True,
        }
        self.log_file_name = "move-{}.log".format(code)
        print("log file: {}".format(self.log_file_name))
        self._camera_conf = {
            "framerate": int(
                os.environ.get("CAMERA_FRAMERATE") or 30),
            "resolution": (640, 480),
        }
        try:
            w, h = map(int, IMAGE_SIZE.split(','))
        except (TypeError, ValueError):
            pass
        else:
            self._camera_conf["resolution"] = (w, h)

    @property
    def is_active(self) -> bool:
        """Check state.
        """
        return bool(self.state.get("active"))

    def stop(self):
        """Change state.
        """
        self.log("termination...")
        self.state["active"] = False

    def log(self, msg, where=None):
        """Show logs
        """
        msg = "[{}]: {}{}".format(
            datetime.now().isoformat()[:19],
            msg,
            " ({})".format(where) if where else "")
        print(msg)
        try:
            with open(self.log_file_name, mode="a") as log_file:
                log_file.write("{}\n".format(msg))
        except Exception as err:
            print(err)

    def photos(self, count=PHOTO_SERIES) -> list:
        """Make photos to files.
        """
        result = []
        call_code = uuid.uuid4().hex[:4]
        result.extend((
            os.path.join(TMP_DIR, "{}_{}{:02}.jpg".format(
                datetime.now().strftime("%d%m%y%H%M%S"),
                call_code,
                index))
            for index in range(count)
        ))

        try:
            with picamera.PiCamera(**self._camera_conf) as cam:
                cam.start_preview()
                time.sleep(0.1)
                cam.capture_sequence(
                    result, use_video_port=True)
                cam.stop_preview()
        except Exception as err:
            self.log(err, "camera")

        return filter(os.path.isfile, result)


manager = SytemManager()


def light_turnon():
    """Pin command for light.
    """
    try:
        # TODO: make one turn on
        # now here is one little diode
        for _ in range(5):
            gpio.output(LIGHT_PIN, True)
            time.sleep(0.1)
            gpio.output(LIGHT_PIN, False)
            time.sleep(0.1)
    except Exception as err:
        manager.log(err, "light turn on")
    return True


def light_turnoff():
    """Pin command for light.
    """
    return True


def finish_handler(signum, frame):
    """SIGINT handler.
    """
    manager.stop()


def prepare():
    """Init GPIO
    """
    try:
        gpio.setmode(gpio.BOARD)
        gpio.setup(SENSOR_PIN, gpio.IN)
        gpio.setup(LIGHT_PIN, gpio.OUT)
    except Exception as err:
        manager.log(err, "prepare GPIO")
    else:
        signal.signal(signal.SIGINT, finish_handler)
        return True


def send_mail(
        send_from,
        send_to,
        subject,
        text,
        files=[],
        server="smtp.gmail.com",
        port=587,
        username="",
        password="",
        isTls=True):
    """Send mail method.
    """
    msg = MIMEMultipart()
    msg["From"] = send_from
    if isinstance(send_to, str):
        send_to = [send_to]

    msg["To"] = COMMASPACE.join(send_to)
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject
    msg.attach(MIMEText(text))

    if files:
        for file_name in files:
            part = MIMEBase("application", "octet-stream")
            with open(file_name, "rb") as img_file:
                part.set_payload(img_file.read())

            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                'attachment; filename="{}"'.format(
                    os.path.basename(file_name)))
            msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if isTls:
        smtp.starttls()
    smtp.login(username or send_from, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


def images(current_dir="./", exts={"jpg", "png", "jpeg", "gif"}):
    """Images files in dir.
    """
    for root, _, files in os.walk(current_dir):
        for file_name in files:
            ext = file_name.rsplit('.', 1)[-1].lower()
            if ext in exts:
                yield path_join(root, file_name)


def send_report(data, photos=None):
    """Prepare and send mail.
    """
    try:
        mail_to = os.environ.get("TO_MAIL")
        manager.log("Report to {} with {} records".format(
            mail_to, len(data)), "send mail")

        send_mail(
            send_from=os.environ.get("FROM_MAIL"),
            password=os.environ.get("PASSWORD_MAIL"),
            send_to=mail_to,
            subject="Movement detected!",
            files=photos,
            text="Movement detected at:\n{}".format(
                "\n".join(map(" {}".format, data))))
    except Exception as err:
        manager.log(err, "send mail")
        return False
    else:
        return True


def monitor_move():
    """Main monitor method.
    """
    last_detect = time.time()
    light_last_on = last_detect - LIGHT_ON_TIME_LIMIT - 1
    data = []
    photos = FileList()

    while manager.is_active:
        try:
            value = gpio.input(SENSOR_PIN)
        except Exception as err:
            manager.log(err, "sensor")
            value = None

        now_time = time.time()

        if value:
            data.append(datetime.now().isoformat())
            manager.log("Detected!", "sensor")
            if light_turnon():
                light_last_on = now_time
                photos.extend(manager.photos())

        if now_time - light_last_on >= LIGHT_ON_TIME_LIMIT:
            light_turnoff()

        if data and now_time - last_detect >= SEND_TIME_INTERVAL_LIMIT:
            last_detect = now_time

            if send_report(data=data, photos=photos):
                data.clear()
                photos.clear()

        time.sleep(0.2)

    if data and send_report(data=data, photos=photos):
        data.clear()
        photos.clear()

prepare() and monitor_move()
