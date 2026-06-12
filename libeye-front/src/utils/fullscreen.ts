export const enterFullScreen = () => {
  const elem = document.documentElement;
  if (elem.requestFullscreen) {
    elem.requestFullscreen().catch(err => {
      console.warn(`Error attempting to enable fullscreen: ${err.message}`);
    });
  }
};

export const exitFullScreen = () => {
  if (document.fullscreenElement) {
    document.exitFullscreen().catch(err => {
      console.warn(`Error attempting to disable fullscreen: ${err.message}`);
    });
  }
};
