import cv2, os, time, torch, requests, pprint, base64
import geocoder

### A class that acts as a processor
class BirdCam():
    def __init__(self):
        self.cam = cv2.VideoCapture(0)
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5m', pretrained=True)
        self.bird_api_url = "https://api.birds.einfachschach.de/v1/predict/birds"
        self.location = self.find_location()

    def __del__(self):
        self.cam.release()

    def process(self):
        while True:
            try:
                result, image = self.cam.read()
                if result:
                    results = self.model(image)
                    res = results.pandas()
                    if 'bird' in str(res.xyxy[0]):
                        self.wait_for__internet_connection()
                        response = self.check_bird(image)
                        pprint.pprint(response)

                else:
                    print("No Cam available. Please! try again")
            except Exception as e:
                print(f"Exception while processing: {e}")
                time.sleep(2)
            time.sleep(1)
    
    def wait_for__internet_connection(self):
        while True:
            try:
                requests.get('https://google.com', timeout=5)
                break
            except requests.exceptions.ConnectionError:
                print("No internet connection. Please connect!")
                time.sleep(5)
        
    
    def find_location(self):
        self.wait_for__internet_connection()
        g = geocoder.ip('me')
        print([g.city, g.latlng])
        return [str(ll) for ll in g.latlng]
    
    def check_bird(self, image):
        print('found bird -> checking it now')
        retval, buffer = cv2.imencode('.png', image)
        jpg_as_b64 = base64.b64encode(buffer)
        jpg_as_text = "data:image/png;base64,"+jpg_as_b64.decode('utf-8')
        response = requests.post(self.bird_api_url, data={"image": jpg_as_text,"location":",".join(self.location),'source':'birdcam'}).json()
        return response

if __name__ == '__main__':
    cam = BirdCam()
    cam.process()