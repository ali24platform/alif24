import React, { useState, useRef, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_MATH_API_URL || 
  (import.meta.env.VITE_API_URL 
    ? import.meta.env.VITE_API_URL.replace('/v1', '/mathkids')
    : "https://alif24.uz/api/mathkids");

function ImageCropper({ onTextExtracted }) {
  const [imageSrc, setImageSrc] = useState(null);
  const [crop, setCrop] = useState({ x: 0, y: 0, width: 0, height: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [loading, setLoading] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [stream, setStream] = useState(null);
  const [rotation, setRotation] = useState(0);
  const imgRef = useRef(null);
  const canvasRef = useRef(null);
  const videoRef = useRef(null);
  const captureCanvasRef = useRef(null);
  const cropContainerRef = useRef(null);

  // Video streamni sozlash
  useEffect(() => {
    if (stream && videoRef.current) {
      try {
        videoRef.current.srcObject = stream;
      } catch (e) {
        console.warn('Video stream sozlanmadi', e);
      }
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  // Boshlang'ich crop o'rnatish
  useEffect(() => {
    if (imageSrc && imgRef.current && crop.width === 0) {
      const img = imgRef.current;
      const rect = img.getBoundingClientRect();
      setCrop({
        x: rect.width * 0.05,
        y: rect.height * 0.1,
        width: rect.width * 0.9,
        height: rect.height * 0.3
      });
    }
  }, [imageSrc]);

  // Rasm yuklash
  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const reader = new FileReader();
      reader.addEventListener('load', () => {
        setImageSrc(reader.result);
        setShowCamera(false);
        setRotation(0);
        setCrop({ x: 0, y: 0, width: 0, height: 0 });
      });
      reader.readAsDataURL(e.target.files[0]);
    }
  };

  // Rasmni chapga aylantirish
  const handleRotateLeft = () => {
    setRotation((prev) => (prev - 90 + 360) % 360);
  };

  // Rasmni o'ngga aylantirish
  const handleRotateRight = () => {
    setRotation((prev) => (prev + 90) % 360);
  };

  // Kamerani to'liq ekranda ochish
  const handleOpenCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        } 
      });
      setStream(mediaStream);
      setShowCamera(true);
      setImageSrc(null);
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      console.error('Kamera ochishda xato:', err);
      alert('Kamera ochib bo\'lmadi. Iltimos, ruxsatni tekshiring.');
    }
  };

  // Rasmga olish
  const handleCapture = () => {
    const video = videoRef.current;
    const canvas = captureCanvasRef.current;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    const imageData = canvas.toDataURL('image/jpeg');
    setImageSrc(imageData);
    handleCloseCamera();
    setRotation(0);
  };

  // Kamerani yopish
  const handleCloseCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    setStream(null);
    setShowCamera(false);
  };

  // Crop boshlanishi
  const handleMouseDown = (e) => {
    e.preventDefault();
    const rect = cropContainerRef.current.getBoundingClientRect();
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top;
    setIsDragging(true);
    setDragStart({ x, y });
    setCrop({ x, y, width: 0, height: 0 });
  };

  // Crop davom etishi
  const handleMouseMove = (e) => {
    if (!isDragging) return;
    e.preventDefault();
    const rect = cropContainerRef.current.getBoundingClientRect();
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top;
    
    setCrop({
      x: Math.min(dragStart.x, x),
      y: Math.min(dragStart.y, y),
      width: Math.abs(x - dragStart.x),
      height: Math.abs(y - dragStart.y)
    });
  };

  // Crop tugashi
  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Crop qilingan rasmni olish
  const getCroppedImage = () => {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    const containerRect = cropContainerRef.current.getBoundingClientRect();
    const imgRect = img.getBoundingClientRect();
    
    const scaleX = img.naturalWidth / imgRect.width;
    const scaleY = img.naturalHeight / imgRect.height;
    
    const offsetX = (imgRect.left - containerRect.left);
    const offsetY = (imgRect.top - containerRect.top);
    
    const cropX = (crop.x - offsetX) * scaleX;
    const cropY = (crop.y - offsetY) * scaleY;
    const cropWidth = crop.width * scaleX;
    const cropHeight = crop.height * scaleY;

    canvas.width = cropWidth;
    canvas.height = cropHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(
      img,
      cropX,
      cropY,
      cropWidth,
      cropHeight,
      0,
      0,
      cropWidth,
      cropHeight
    );

    return new Promise((resolve) => {
      canvas.toBlob(
        (blob) => {
          resolve(blob);
        },
        'image/jpeg',
        0.95
      );
    });
  };

  // Masalani ajratib olish
  const handleExtractProblem = async () => {
    if (!imageSrc) {
      alert('Iltimos, avval rasm tanlang!');
      return;
    }

    setLoading(true);

    try {
      let imageBlob;

      if (crop.width > 10 && crop.height > 10) {
        imageBlob = await getCroppedImage();
      } else {
        const response = await fetch(imageSrc);
        imageBlob = await response.blob();
      }

      const formData = new FormData();
      formData.append('image', imageBlob, 'cropped-image.jpg');

      const res = await fetch(`${API_BASE_URL}/image/read`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Server xatosi: ${res.status}`);
      }

      const data = await res.json();
      
      if (data.success && data.text) {
        if (onTextExtracted) {
          onTextExtracted(data.text);
        }
        alert('Masala muvaffaqiyatli o\'qildi!');
      } else {
        alert(data.error || 'Masala o\'qishda xatolik');
      }
    } catch (err) {
      console.error('Xato:', err);
      alert(`Masala o'qishda xatolik: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Rasmni reset qilish
  const handleResetImage = () => {
    setImageSrc(null);
    setCrop({ x: 0, y: 0, width: 0, height: 0 });
    setRotation(0);
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    setStream(null);
    setShowCamera(false);
  };

  return (
    <div >
      {/* Header */}
 

      {/* Asosiy tugmalar */}
      {!showCamera && (
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
          <button 
            onClick={handleOpenCamera}
            className="px-8 py-3 bg-gradient-to-r from-blue-400 to-cyan-400 text-white text-lg font-bold rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300"
          >
            📷 Kamera ochish
          </button>
          <label className="px-8 py-3 bg-white text-purple-600 text-lg font-bold rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 cursor-pointer text-center">
            📁 Fayl yuklash
            <input
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>
        </div>
      )}

      {/* To'liq ekran kamera */}
     {showCamera && (
  <div className="fixed inset-0 bg-black z-50 flex flex-col">
    <video
      ref={videoRef}
      autoPlay
      muted
      playsInline
      className="flex-1 w-full h-full object-cover"
    />
    
    {/* Yopish tugmasi - tepa ung burchakda */}
    <button 
      onClick={handleCloseCamera}
      className="absolute top-0 right-0 text-white text-lg font-bold rounded-full shadow-lg hover:bg-red-600 transition-all duration-300"
      style={{ paddingTop: '15px', paddingRight: '15px', margin: '15px' }}
    >
      ❌
    </button>

    {/* Suratga olish tugmasi - pastda markazda */}
    <div className="absolute bottom-0 left-0 right-0 flex justify-center" style={{ paddingBottom: '110px' }}>
      <button 
        onClick={handleCapture}
        className="w-20 h-20 bg-gradient-to-r from-green-400 to-cyan-400 text-white text-3xl rounded-full shadow-2xl hover:shadow-xl transform hover:scale-105 transition-all duration-300 flex items-center justify-center"
      >
        📸
      </button>
    </div>
  </div>
)}
      {/* Rasm kesish qismi */}
      {imageSrc && !showCamera && (
        <div className="space-y-5 pb-20">
          <div 
            ref={cropContainerRef}
            className="bg-white p-5 rounded-2xl overflow-auto flex justify-center items-center relative select-none"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onTouchStart={handleMouseDown}
            onTouchMove={handleMouseMove}
            onTouchEnd={handleMouseUp}
          >
            <img
              ref={imgRef}
              src={imageSrc}
              alt="Yuklangan rasm"
              style={{ 
                transform: `rotate(${rotation}deg)`,
                maxWidth: '100%',
                maxHeight: '500px'
              }}
              className="block pointer-events-none"
            />
            
            {/* Crop overlay */}
            {crop.width > 0 && crop.height > 0 && (
              <div
                className="absolute border-3 border-dashed border-purple-600 bg-purple-200/20 pointer-events-none"
                style={{
                  left: `${crop.x}px`,
                  top: `${crop.y}px`,
                  width: `${crop.width}px`,
                  height: `${crop.height}px`
                }}
              >
                <div className="absolute -top-1 -left-1 w-3 h-3 bg-purple-600 rounded-full"></div>
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-purple-600 rounded-full"></div>
                <div className="absolute -bottom-1 -left-1 w-3 h-3 bg-purple-600 rounded-full"></div>
                <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-purple-600 rounded-full"></div>
              </div>
            )}
          </div>

          <div className="text-center  text-black text-sm opacity-75">
            💡 Masalani kesish uchun sichqoncha yoki barmoq bilan tortib belgilang
          </div>

          {/* Boshqaruv tugmalari */}
          <div className="flex flex-wrap gap-3 justify-center p-5 bg-white/10 rounded-2xl">
         
            <button 
              onClick={handleExtractProblem}
              disabled={loading}
              className="px-10 py-4 bg-gradient-to-r from-pink-400 to-red-500 text-white font-bold text-base rounded-xl shadow-md hover:shadow-lg transform hover:-translate-y-1 transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading ? '⏳ O\'qilmoqda...' : '🔍 Masalani o\'qish'}
            </button>
            <button 
              onClick={handleResetImage}
              className="px-8 py-3 bg-white text-purple-600 border-2 border-purple-600 font-bold rounded-xl shadow-md hover:bg-purple-600 hover:text-white transform hover:-translate-y-1 transition-all duration-300"
            >
              🔄 Yangidan boshlash
            </button>
          </div>
        </div>
      )}

      {/* Yashirin canvaslar */}
      <canvas ref={canvasRef} className="hidden" />
      <canvas ref={captureCanvasRef} className="hidden" />
    </div>
  );
}

export default ImageCropper;