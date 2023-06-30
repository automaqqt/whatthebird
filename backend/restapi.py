import argparse
import io
import ssl, base64, time

import torch
from flask import Flask, request
from PIL import Image
from flask_cors import CORS

ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)
models = {}
CORS(app)

DETECTION_URL = "/v1/birds"


@app.route(DETECTION_URL, methods=["POST"])
def predict():
    if request.method != "POST":
        return

    if request.values.get("image"):
        im_b64 = request.values.get("image").split(",")[1]
        imgdata = base64.b64decode(str(im_b64))
        img = Image.open(io.BytesIO(imgdata))
        results = models['birds'](img, size=640)
        results_json = results.pandas().xyxy[0].to_json(orient="records")
        if not len(results_json) > 2:
            res_norm = models['yolo_base'](img, size=640)
            norm_results = res_norm.pandas().xyxy[0]
            if 'bird' in str(norm_results):
                print('found a non detectable bird, saving it to disk')
                stamp = f"{int(time.time())}_{str(im_b64)[-20:-2]}"
                birds = []
                w, h = img.size
                for tens in res_norm.xyxy[0].tolist():
                    if tens[-1] == 14.0:

                        xmin = tens[0]
                        xmax = tens[2]
                        width = xmax-xmin
                        ymin = tens[1]
                        ymax = tens[3]
                        height = ymax-ymin

                        centerx = xmin+((width)/2)
                        centery = ymin+((height)/2)

                        birds.append(f'{round(centerx/w,5)} {round(centery/h,5)} {round(width/w,5)} {round(height/h,5)}')

                img.save(f'data/not_sorted/images/{stamp}.jpg')
                with open(f'data/not_sorted/labels/{stamp}.txt','w+') as e:
                    for bird in birds:
                        e.write(bird+'\n')

        return results_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Für die Vögel")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    opt = parser.parse_args()

    models['birds'] = torch.hub.load("ultralytics/yolov5",'custom', path='ger_birds_largel1.pt', force_reload=True, skip_validation=True)
    models['yolo_base'] = torch.hub.load("ultralytics/yolov5",'yolov5l', force_reload=True, skip_validation=True)

    app.run(host="0.0.0.0", port=opt.port) 
