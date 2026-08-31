import React from 'react';

const Toast = ({ message, type }) => {
  const isError = type === 'error';
  return (
    <div className={`fixed top-4 right-4 p-4 rounded shadow-lg text-white font-body-md z-50 transition-opacity duration-300 ${isError ? 'bg-error' : 'bg-green-600'}`}>
      {message}
    </div>
  );
};

export default Toast;
