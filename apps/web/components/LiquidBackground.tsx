"use client";

// Global water-surface background. One fixed-position WebGL canvas mounted in
// the root layout; runs a small fragment shader that draws procedurally-
// animated water tinted by the brand palette, and that "leans" in the
// direction the cursor is moving (currents tuning, see plan in
// notes/00 -> root plan files). When WebGL is unavailable, falls back to the
// DOM-orb implementation in LiquidBackgroundFallback so the page still has a
// soft animated background instead of a flat colour.
//
// Layer model: canvas sits at z-index -10 behind every page, with
// mix-blend-mode: soft-light so it blends with the neutral body background
// and with any visible bg-surface margins between cards. Opaque cards
// (bg-surface) intentionally hide the canvas in their footprint.

import { useEffect, useRef, useState } from "react";
import LiquidBackgroundFallback from "./LiquidBackgroundFallback";

const VERTEX_SHADER = `
attribute vec2 aPosition;
void main() {
  gl_Position = vec4(aPosition, 0.0, 1.0);
}
`;

// 3D value noise sampled with z = time. Instead of scrolling a 2D field
// past the camera, the shader samples a continuous 3D noise volume and
// advances the z coordinate each frame. The result: each (x, y) point's
// noise value smoothly evolves over time, so the visible blobs morph in
// place (grow, merge, split, dissolve) rather than translate across the
// page. Single blue palette; no warm overlay; cursor still has a gentle
// influence on the xy sampling coords near the pointer.
const FRAGMENT_SHADER = `
precision mediump float;
uniform float uTime;
uniform vec2 uResolution;
uniform vec2 uCursor;
uniform vec2 uFlow;
uniform float uIntensity;

float hash3(vec3 p) {
  return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

// 3D value noise: trilinear interpolation of 8 corner hashes per cell.
float vnoise3(vec3 p) {
  vec3 i = floor(p);
  vec3 f = fract(p);
  vec3 u = f * f * (3.0 - 2.0 * f);
  float n000 = hash3(i + vec3(0.0, 0.0, 0.0));
  float n100 = hash3(i + vec3(1.0, 0.0, 0.0));
  float n010 = hash3(i + vec3(0.0, 1.0, 0.0));
  float n110 = hash3(i + vec3(1.0, 1.0, 0.0));
  float n001 = hash3(i + vec3(0.0, 0.0, 1.0));
  float n101 = hash3(i + vec3(1.0, 0.0, 1.0));
  float n011 = hash3(i + vec3(0.0, 1.0, 1.0));
  float n111 = hash3(i + vec3(1.0, 1.0, 1.0));
  return mix(
    mix(mix(n000, n100, u.x), mix(n010, n110, u.x), u.y),
    mix(mix(n001, n101, u.x), mix(n011, n111, u.x), u.y),
    u.z
  );
}

float fbm3(vec3 p) {
  float v = 0.0;
  float a = 0.5;
  for (int i = 0; i < 3; i++) {
    v += a * vnoise3(p);
    p = p * 2.07 + vec3(1.7, 2.3, 0.9);
    a *= 0.5;
  }
  return v;
}

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution;
  vec2 aspect = vec2(uResolution.x / max(uResolution.y, 1.0), 1.0);
  vec2 p = uv * aspect;

  // Multi-scale 3D noise: a macro layer carries the big-blob structure,
  // a higher-frequency layer rides on top to break up the macro blobs into
  // smaller ones and keep the field always animating somewhere. Different
  // z speeds so the two layers never morph in sync — the smaller features
  // evolve faster, which reads as "persistent flow". Cursor uniforms
  // (uCursor / uFlow) are intentionally NOT sampled here: the cursor should
  // not affect the flow.
  vec3 q1 = vec3(p * 3.2, uTime * 0.22);
  vec3 q2 = vec3(p * 7.0 + vec2(3.7, 1.9), uTime * 0.32 + 5.0);
  float n = 0.65 * fbm3(q1) + 0.45 * fbm3(q2);
  n = clamp(n - 0.05, 0.0, 1.0);

  // Navy palette: cool pale -> saturated blue -> deep navy. The thresholds
  // are tightened (deep range starts earlier) so more of the surface lands
  // in the navy register instead of the lighter ends.
  vec3 paleA = vec3(0.72, 0.82, 0.93);
  vec3 paleB = vec3(0.30, 0.50, 0.78);
  vec3 deepB = vec3(0.06, 0.18, 0.42);

  vec3 color = mix(paleA, paleB, smoothstep(0.18, 0.50, n));
  color = mix(color, deepB, smoothstep(0.50, 0.85, n));

  gl_FragColor = vec4(color, uIntensity);
}
`;

// Middle-ground tuning: visible enough to clearly tint the page light blue
// without the previous explicit "currents" energy. Cursor still nudges the
// local flow, but at half the energy of the explicit pass.
const CURSOR_SMOOTH = 0;
const CURRENT_GAIN = 0.6;
const FLOW_DECAY = 0.94;
const FLOW_CLAMP = 0.35;
const INTENSITY = 1;

function compileShader(
  gl: WebGLRenderingContext,
  type: number,
  src: string,
): WebGLShader | null {
  const sh = gl.createShader(type);
  if (!sh) return null;
  gl.shaderSource(sh, src);
  gl.compileShader(sh);
  if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
    // eslint-disable-next-line no-console
    console.warn("[liquid] shader compile failed:", gl.getShaderInfoLog(sh));
    gl.deleteShader(sh);
    return null;
  }
  return sh;
}

function clamp(value: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, value));
}

export default function LiquidBackground() {
  // null = probing, true = WebGL path active, false = fallback path active.
  const [webglOk, setWebglOk] = useState<boolean | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    const gl = canvas.getContext("webgl", {
      alpha: true,
      antialias: false,
      premultipliedAlpha: true,
    }) as WebGLRenderingContext | null;
    if (!gl) {
      setWebglOk(false);
      return;
    }

    const vs = compileShader(gl, gl.VERTEX_SHADER, VERTEX_SHADER);
    const fs = compileShader(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER);
    const program = gl.createProgram();
    if (!vs || !fs || !program) {
      setWebglOk(false);
      return;
    }
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      // eslint-disable-next-line no-console
      console.warn("[liquid] program link failed:", gl.getProgramInfoLog(program));
      setWebglOk(false);
      return;
    }
    setWebglOk(true);
    gl.useProgram(program);

    // Fullscreen quad in clip space.
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
      gl.STATIC_DRAW,
    );
    const aPosition = gl.getAttribLocation(program, "aPosition");
    gl.enableVertexAttribArray(aPosition);
    gl.vertexAttribPointer(aPosition, 2, gl.FLOAT, false, 0, 0);

    const uTime = gl.getUniformLocation(program, "uTime");
    const uResolution = gl.getUniformLocation(program, "uResolution");
    const uCursor = gl.getUniformLocation(program, "uCursor");
    const uFlow = gl.getUniformLocation(program, "uFlow");
    const uIntensity = gl.getUniformLocation(program, "uIntensity");

    gl.uniform1f(uIntensity, INTENSITY);

    // State carried across rAF ticks. Plain locals + a closure so we don't
    // pay React re-render cost on every mouse move or frame.
    const target = { x: 0.5, y: 0.5 };
    const cursor = { x: 0.5, y: 0.5 };
    const flow = { x: 0, y: 0 };
    let lastRaw = { x: 0.5, y: 0.5, t: 0 };
    let startTime = 0;
    let lastFrame = 0;
    let raf = 0;

    function resize() {
      if (!gl) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      const w = Math.max(1, Math.floor(window.innerWidth * dpr));
      const h = Math.max(1, Math.floor(window.innerHeight * dpr));
      if (canvas!.width !== w || canvas!.height !== h) {
        canvas!.width = w;
        canvas!.height = h;
      }
      gl.viewport(0, 0, w, h);
      gl.uniform2f(uResolution, w, h);
    }

    function onMove(event: MouseEvent) {
      const nx = event.clientX / window.innerWidth;
      // GL has +Y up; CSS has +Y down. Flip so cursor maps intuitively
      // when read in the shader.
      const ny = 1 - event.clientY / window.innerHeight;
      target.x = nx;
      target.y = ny;
      const now = performance.now();
      const dt = Math.max(1, now - lastRaw.t);
      // Velocity in UV units per ~16ms (one frame at 60fps). Multiplied by
      // CURRENT_GAIN and added cumulatively so a sustained drag piles up
      // more flow than a single twitch.
      const vx = ((nx - lastRaw.x) * 16) / dt;
      const vy = ((ny - lastRaw.y) * 16) / dt;
      flow.x = clamp(flow.x + vx * CURRENT_GAIN, -FLOW_CLAMP, FLOW_CLAMP);
      flow.y = clamp(flow.y + vy * CURRENT_GAIN, -FLOW_CLAMP, FLOW_CLAMP);
      lastRaw = { x: nx, y: ny, t: now };
    }

    function onLeaveWindow() {
      // Cursor left the viewport; kill the current so an idle window
      // doesn't keep churning a stale flow vector.
      flow.x = 0;
      flow.y = 0;
    }

    function tick(now: number) {
      if (!gl) return;
      lastFrame = now;
      cursor.x += (target.x - cursor.x) * CURSOR_SMOOTH;
      cursor.y += (target.y - cursor.y) * CURSOR_SMOOTH;
      flow.x *= FLOW_DECAY;
      flow.y *= FLOW_DECAY;
      gl.uniform1f(uTime, (now - startTime) / 1000);
      gl.uniform2f(uCursor, cursor.x, cursor.y);
      gl.uniform2f(uFlow, flow.x, flow.y);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      raf = requestAnimationFrame(tick);
    }

    function renderStaticFrame() {
      if (!gl) return;
      gl.uniform1f(uTime, 0);
      gl.uniform2f(uCursor, 0.5, 0.5);
      gl.uniform2f(uFlow, 0, 0);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    }

    function startLoop() {
      if (raf || reducedMotion) return;
      startTime = performance.now();
      lastFrame = startTime;
      raf = requestAnimationFrame(tick);
    }
    function stopLoop() {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
    }

    function onVisibility() {
      if (document.visibilityState === "visible") {
        startLoop();
      } else {
        stopLoop();
      }
    }

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", onMove);
    // mouseleave on <html> fires when the cursor exits the viewport.
    document.documentElement.addEventListener("mouseleave", onLeaveWindow);
    document.addEventListener("visibilitychange", onVisibility);

    if (reducedMotion) {
      renderStaticFrame();
    } else {
      startLoop();
    }

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
      document.documentElement.removeEventListener("mouseleave", onLeaveWindow);
      document.removeEventListener("visibilitychange", onVisibility);
      stopLoop();
      gl.deleteBuffer(buffer);
      gl.deleteProgram(program);
      gl.deleteShader(vs);
      gl.deleteShader(fs);
    };
  }, []);

  if (webglOk === false) {
    return <LiquidBackgroundFallback />;
  }

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10"
      style={{ width: "100vw", height: "100vh" }}
    />
  );
}
