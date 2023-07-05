import argparse
import io
import ssl, base64, time

import torch
from flask import Flask, request
from PIL import Image
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
models = {}
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///birds.sqlite3'

db = SQLAlchemy(app)

class Bird(db.Model):
    id = db.Column(db.String(200), primary_key = True)
    source = db.Column(db.String(200))
    date = db.Column(db.String(100))
    location = db.Column(db.String(200)) 
    detected = db.Column(db.Boolean()) 
    results = db.Column(db.String(1000))

    def __init__(self, id, source, date, location,detected, results):
        self.id = id
        self.source = source
        self.date = date
        self.location = location
        self.detected = detected
        self.results = results
    
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

def commit_to_database(bird):
    db.session.add(bird)
    db.session.commit()

@app.route("/v1/predict/birds", methods=["POST"])
def predict():
    if request.values.get("image"):
        detected = True
        im_b64 = request.values.get("image").split(",")[1]
        imgdata = base64.b64decode(str(im_b64))
        img = Image.open(io.BytesIO(imgdata))
        results = models['birds'](img, size=640)
        results_json = results.pandas().xyxy[0].to_json(orient="records")
        stamp = f"{int(time.time())}_{str(im_b64)[-20:-2].replace('/','')}"
        if not len(results_json) > 2:
            detected = False
            res_norm = models['yolo_base'](img, size=640)
            norm_results = res_norm.pandas().xyxy[0]
            if 'bird' in str(norm_results):
                print('found a non detectable bird, saving it to disk')
                
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

                img.save(f'data/not_sorted/images/{stamp}.png')
                with open(f'data/not_sorted/labels/{stamp}.txt','w+') as e:
                    for bird in birds:
                        e.write(bird+'\n')
                
        commit_to_database(
                Bird(
                    id=stamp,
                    source=f"{request.values.get('source','webpage')}",
                    date=f"{time.strftime('%Y-%m-%d %H:%M:%S')}",
                    location=f"{request.values.get('location','none')}",
                    detected=detected,
                    results=f"{results_json}"
                )
            )

        return results_json
    
    return {"error":"No image"}

@app.route("/v1/data/get_single/<string:id>", methods=["GET"])
def get_bird(id):
    bird = db.get_or_404(Bird, id)
    return {'results':bird.as_dict()}

@app.route("/v1/data/get_all", methods=["GET"])
def get_all_bird():
    all_birds = db.session.query(Bird).all()
    return {'results':[bird.as_dict() for bird in all_birds]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Für die Vögel")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    opt = parser.parse_args()

    models['birds'] = torch.hub.load("ultralytics/yolov5",'custom', path='ger_birds_largel1.pt', force_reload=True, skip_validation=True)
    models['yolo_base'] = torch.hub.load("ultralytics/yolov5",'yolov5l', force_reload=True, skip_validation=True)

    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=opt.port) 
    
