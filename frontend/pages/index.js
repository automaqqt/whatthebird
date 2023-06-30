import React, { useState, useEffect, useRef } from 'react';
import { Button, Box, Typography, IconButton, Link, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { Settings } from '@mui/icons-material';
import CameraswitchIcon from '@mui/icons-material/Cameraswitch';
import CircularProgress from '@mui/material/CircularProgress';
import axios from 'axios';
import logo from '../public/logo.png';
import Image from 'next/image';

const BirdDetectionPage = () => {
  const [cam, setCam] = useState('environment');
  const [result, setResult] = useState({});
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [waiting, setWaiting] = useState(false);

  const handleClose = () => {
    setOpen(false);
    setResult({});
  };

  const nextCam = () => {
    setCam(cam === 'environment' ? 'user' : 'environment');
  };

  const getFormattedUrl = (bird) => {
    return `https://wikipedia.org/wiki/${bird}`;
  };

  const uploadImageToApi = (imageData) => {

    const formData = new FormData();
    formData.append("image", imageData);
    axios.post('https://api.birds.einfachschach.de/v1/birds', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
    })
    .then(response => {
      console.log('Image uploaded successfully:', response);
      if (response.data.length > 0) {
        setResult(response.data[0]);
      }

      setOpen(true);

      setWaiting(false);
      
    })
    .catch(error => {
      console.error('Error uploading image:', error);

      setWaiting(false);
    });

  }

  const handleImageUpload = (event) => {

    setWaiting(true);
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        uploadImageToApi(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {

      setWaiting(true);
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      const imageDataURL = canvas.toDataURL('image/png');
      uploadImageToApi(imageDataURL);
    }
  };

  useEffect(() => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: {facingMode: cam} })
        .then((stream) => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
        })
        .catch((error) => {
          console.error('Error accessing camera:', error);
        });
    }
  }, [waiting]);

  const dialogStyle = {
    maxWidth: '400px',
    borderRadius: '8px',
    overflow: 'hidden',
  };

  const dialogTitleStyleSuccess = {
    backgroundColor: 'green',
    color: '#fff',
    padding: '16px',
    fontFamily: 'Arial, sans-serif',
    fontWeight: 'bold',
  };

  const dialogTitleStyleFail = {
    backgroundColor: '#f50057',
    color: '#fff',
    padding: '16px',
    fontFamily: 'Arial, sans-serif',
    fontWeight: 'bold',
  };

  const dialogContentStyle = {
    padding: '16px',
    marginBottom: '15px',
    fontFamily: 'Arial, sans-serif',
  };

  const closeButtonStyle = {
    color: 'white',
    position: 'absolute',
    right:0,
    top:5,
    fontWeight: 'bold',
    fontSize: 20,
  };

  const viewButtonStyle = {
    backgroundColor: 'green',
    color: '#fff',
    marginLeft: '15px',
  };

    return (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          minHeight="100vh"
          textAlign="center"
        >
          <Image
                src={logo}
                width={75}
                style={{ position: 'absolute', top: 8, left:8}}
              />
              <IconButton
              sx={{ position: 'absolute', top: 12, right: 12, color: '#fff', backgroundColor: 'rgba(0, 0, 0, 0.6)' }}
              aria-label="Settings"
              onClick={() => nextCam()}
            >
              <Settings  />
            </IconButton>
            {waiting ? <CircularProgress /> :
            <Box position="relative" width={400} height={300} boxShadow={4} borderRadius={8} overflow="hidden">
            <video ref={videoRef} autoPlay style={{ width: '100%', height: '100%' }} />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            <IconButton
              sx={{ position: 'absolute', top: 8, right: 8, color: '#fff', backgroundColor: 'rgba(0, 0, 0, 0.6)' }}
              aria-label="Settings"
              onClick={() => nextCam()}
            >
              <CameraswitchIcon />
            </IconButton>
          </Box>}
          
          <Box mt={2}>
            <Button variant="contained" disabled={waiting}  sx={{borderRadius:7,backgroundColor:'green', width:300, height:60, fontSize:20}} onClick={capturePhoto}>
              Check that bird!
            </Button>
          </Box>
          <Typography variant="subtitle1"  mt={2}>
            or
            </Typography> 
          <Box mt={2}>
              <input
            type="file"
            accept="image/*"
            id="image-upload"
            style={{ display: 'none' }}
            onChange={handleImageUpload}
          />
          
          <label htmlFor="image-upload">
            <Button variant="contained" disabled={waiting} component="span" mt={2} sx={{borderRadius:7,backgroundColor:'grey', width:300, height:60, fontSize:20}}>
              Upload Picture
            </Button>
          </label>
          </Box>
          
          <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth >
            {!result.name ? 
            <>
                <DialogTitle style={dialogTitleStyleFail}>
                    {'No bird found :('}
                    <Button onClick={handleClose} style={closeButtonStyle}>
                      X
                    </Button>
                  </DialogTitle>
                <DialogContent style={dialogContentStyle}>
                  <Typography variant="body2" color="textSecondary">
                    You can try again. We try to get better and learn about your bird.
                  </Typography>
                </DialogContent>
            </> : 
            <>
              <DialogTitle style={dialogTitleStyleSuccess}>
                Look what we found! 
                <Button onClick={handleClose} style={closeButtonStyle}>
                  X
                </Button>
              </DialogTitle>
                <DialogContent style={dialogContentStyle}>
                  <Box display="flex" flexDirection="row" alignItems="center" justifyContent="center">
                    <Typography variant="body1" gutterBottom style={{ fontFamily: 'Arial, sans-serif' }}>
                    {result.name} ({(result.confidence * 100).toFixed(2)}%)
                    </Typography>
                    <Button
                      variant="contained"
                      href={getFormattedUrl(result.name)}
                      target="_blank"
                      rel="noopener"
                      style={viewButtonStyle}
                    >
                      Wikipedia
                    </Button>
                  </Box>
                </DialogContent>
                <Typography variant="body2" color="textSecondary" style={{ position:'absolute',fontFamily: 'Arial, sans-serif', right:4, bottom:2 }}>
                    {'Thats not correct? Please contact us <3'}
                </Typography>
            </>}
          </Dialog>
        </Box>
      );
};

export default BirdDetectionPage;
