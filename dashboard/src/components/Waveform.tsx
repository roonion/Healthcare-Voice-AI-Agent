import { useRef, useEffect } from "react";

interface Props {
  active: boolean;
}

export function Waveform({ active }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };
    resize();
    window.addEventListener("resize", resize);

    let phase = 0;

    const draw = () => {
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      ctx.clearRect(0, 0, w, h);

      if (!active) {
        ctx.strokeStyle = "#374151";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, h / 2);
        ctx.lineTo(w, h / 2);
        ctx.stroke();
        animationRef.current = requestAnimationFrame(draw);
        return;
      }

      phase += 0.04;
      const gradient = ctx.createLinearGradient(0, 0, w, 0);
      gradient.addColorStop(0, "#06b6d4");
      gradient.addColorStop(0.5, "#8b5cf6");
      gradient.addColorStop(1, "#06b6d4");

      ctx.strokeStyle = gradient;
      ctx.lineWidth = 2;
      ctx.beginPath();

      for (let x = 0; x < w; x++) {
        const t = x / w;
        const amplitude =
          Math.sin(t * Math.PI) * (h * 0.35) * (0.5 + 0.5 * Math.sin(phase * 0.7));
        const y =
          h / 2 +
          amplitude *
            (Math.sin(t * 8 + phase) * 0.5 +
              Math.sin(t * 12 + phase * 1.3) * 0.3 +
              Math.sin(t * 20 + phase * 2.1) * 0.2);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animationRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [active]);

  return (
    <div className="h-full flex items-center px-4">
      <canvas ref={canvasRef} className="w-full h-16" />
    </div>
  );
}
