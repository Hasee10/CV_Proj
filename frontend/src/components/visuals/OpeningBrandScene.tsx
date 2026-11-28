import { useEffect, useRef, type MutableRefObject } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { MeshSurfaceSampler } from "three/addons/math/MeshSurfaceSampler.js";
import { ease, openingPose, openingProgress, type OpeningSceneState } from "./openingMotion";

// Union outline of the two paths in public/brand/mark.svg. A single extrusion
// avoids intersecting faces where the bracket meets the check.
export function createBrandGeometry() {
  const outline = [[8, 8], [31, 8], [31, 18], [18, 18], [18, 46],
    [26, 46], [20, 40], [26, 32], [36, 42], [55, 15], [63, 21],
    [37, 57], [31, 51], [31, 56], [8, 56]];
  const shape = new THREE.Shape();
  outline.forEach(([x, y], i) => {
    const px = (x - 35.5) / 49, py = (32.5 - y) / 49;
    if (i === 0) shape.moveTo(px, py); else shape.lineTo(px, py);
  });
  shape.closePath();
  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth: 0.19, bevelEnabled: true, bevelSegments: 4,
    bevelSize: 0.014, bevelThickness: 0.014, steps: 1,
  });
  geometry.translate(0, 0, -0.095);
  return geometry;
}

// A closed strip, with an actual thin edge and a rotating cross-section.
function ribbonGeometry(offset: number, width: number) {
  const positions: number[] = [], uv: number[] = [], indices: number[] = [];
  const segments = 160;
  for (let i = 0; i <= segments; i++) {
    const t = i / segments, u = t * 2 - 1;
    const x = u * 9.5, y = Math.sin(u * 2.7 + offset) * 2.5 + u * 1.2;
    const z = Math.cos(u * 3.1 + offset) * 1.15;
    const tangent = new THREE.Vector3(19, Math.cos(u * 2.7 + offset) * 13.5 + 2.4,
      -Math.sin(u * 3.1 + offset) * 7.13).normalize();
    const across = new THREE.Vector3(-tangent.y, tangent.x, 0).normalize();
    across.applyAxisAngle(tangent, Math.sin(t * Math.PI * 2 + offset) * 0.9);
    const normal = new THREE.Vector3().crossVectors(tangent, across).normalize();
    for (const [side, edge] of [[-1, 1], [1, 1], [1, -1], [-1, -1]]) {
      positions.push(x + across.x * side * width / 2 + normal.x * edge * 0.018,
        y + across.y * side * width / 2 + normal.y * edge * 0.018,
        z + across.z * side * width / 2 + normal.z * edge * 0.018);
      uv.push(t, (side + 1) / 2);
    }
    if (i < segments) for (let side = 0; side < 4; side++) {
      const a = i * 4 + side, b = i * 4 + (side + 1) % 4;
      indices.push(a, b, a + 4, b, b + 4, a + 4);
    }
  }
  const end = segments * 4;
  indices.push(0, 3, 1, 1, 3, 2, end, end + 1, end + 3, end + 1, end + 2, end + 3);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

export default function OpeningBrandScene({ state, wake }: {
  state: MutableRefObject<OpeningSceneState>;
  wake: MutableRefObject<() => void>;
}) {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = host.current!, stage = el.closest<HTMLElement>(".depth-stage")!;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "low-power" });
    } catch {
      stage.dataset.brandScene = "fallback";
      return;
    }
    const dpr = Math.min(devicePixelRatio, innerWidth < 600 ? 1.35 : 1.6);
    renderer.setPixelRatio(dpr);
    renderer.setClearColor(0, 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.95;
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-8, 8, 5, -5, 0.1, 100);
    camera.position.z = 30;
    const pmrem = new THREE.PMREMGenerator(renderer), room = new RoomEnvironment();
    const environment = pmrem.fromScene(room, 0.04);
    scene.environment = environment.texture;
    room.dispose(); pmrem.dispose();
    scene.add(new THREE.HemisphereLight("#fff9ef", "#a695b4", 0.9));
    const key = new THREE.DirectionalLight("#fff8e8", 2.3);
    key.position.set(-4, 6, 9); scene.add(key);
    const rim = new THREE.DirectionalLight("#d9c5fa", 1.4);
    rim.position.set(5, 0, 2); scene.add(rim);

    const ribbons = new THREE.Group();
    scene.add(ribbons);
    const geometries: THREE.BufferGeometry[] = [], materials: THREE.Material[] = [];
    const ribbonSettings = [
      { color: "#718e77", offset: 0.1, width: 0.94, x: -0.9, y: 1.35, z: 3, angle: -0.3, dir: -1 },
      { color: "#a88cbd", offset: 2.9, width: 0.72, x: 1.5, y: -0.95, z: -1, angle: 0.16, dir: 1 },
      { color: "#e8dfd2", offset: 1.9, width: 1.16, x: -0.3, y: -1.9, z: -5, angle: -0.4, dir: -1 },
      { color: "#8a759f", offset: 4.3, width: 0.25, x: 0.8, y: 2.5, z: -9, angle: 0.3, dir: 1 },
    ];
    const strips = ribbonSettings.map((s) => {
      const geo = ribbonGeometry(s.offset, s.width); geometries.push(geo);
      const material = new THREE.MeshPhysicalMaterial({
        color: s.color, metalness: 0.32, roughness: 0.29, clearcoat: 0.8,
        clearcoatRoughness: 0.22, side: THREE.DoubleSide, envMapIntensity: 0.65,
      });
      // Fine woven edge, without text or an extra texture request.
      material.onBeforeCompile = (shader) => {
        shader.vertexShader = "varying vec2 vStripUv;\n" + shader.vertexShader;
        shader.vertexShader = shader.vertexShader.replace("#include <uv_vertex>", "#include <uv_vertex>\nvStripUv = uv;");
        shader.fragmentShader = "varying vec2 vStripUv;\n" + shader.fragmentShader;
        shader.fragmentShader = shader.fragmentShader.replace("#include <color_fragment>", `#include <color_fragment>
          float selvage = smoothstep(.94,.975,abs(vStripUv.y-.5)*2.);
          float hairline = smoothstep(.006,.002,abs(abs(vStripUv.y-.5)-.455));
          diffuseColor.rgb *= mix(1.,.57,selvage);
          diffuseColor.rgb = mix(diffuseColor.rgb,vec3(.94,.91,.87),hairline*.75);`);
      };
      materials.push(material);
      const mesh = new THREE.Mesh(geo, material);
      ribbons.add(mesh);
      return mesh;
    });

    const emblem = new THREE.Group(); scene.add(emblem);
    const brandGeo = createBrandGeometry(); geometries.push(brandGeo);
    const reveal = { value: 0 };
    const brandMaterial = new THREE.MeshPhysicalMaterial({
      color: "#92b08b", metalness: 0.62, roughness: 0.22,
      clearcoat: 1, clearcoatRoughness: 0.17, transparent: true,
      envMapIntensity: 0.8,
    });
    brandMaterial.onBeforeCompile = (shader) => {
      shader.uniforms.uReveal = reveal;
      shader.fragmentShader = "uniform float uReveal;\n" + shader.fragmentShader;
      shader.fragmentShader = shader.fragmentShader.replace("#include <clipping_planes_fragment>", `#include <clipping_planes_fragment>
        float grain = fract(sin(dot(floor(gl_FragCoord.xy),vec2(12.9898,78.233)))*43758.5453);
        if(grain > uReveal) discard;`);
    };
    const edgeMaterial = brandMaterial.clone();
    edgeMaterial.color.set("#3f6757"); edgeMaterial.roughness = 0.26;
    edgeMaterial.onBeforeCompile = brandMaterial.onBeforeCompile;
    materials.push(brandMaterial, edgeMaterial);
    const solid = new THREE.Mesh(brandGeo, [brandMaterial, edgeMaterial]); emblem.add(solid);

    let seed = 41;
    const random = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
    const count = innerWidth < 600 ? 3800 : 6800;
    const positions = new Float32Array(count * 3), scatter = new Float32Array(count * 3), seeds = new Float32Array(count);
    // Three r182 supports this method; the matching @types declaration omits it.
    const sampler = new MeshSurfaceSampler(solid) as MeshSurfaceSampler & {
      setRandomGenerator(fn: () => number): MeshSurfaceSampler;
    };
    sampler.setRandomGenerator(random).build();
    const point = new THREE.Vector3();
    for (let i = 0; i < count; i++) {
      sampler.sample(point); point.toArray(positions, i * 3);
      const angle = random() * Math.PI * 2, radius = 0.8 + random() * 1.4;
      scatter.set([Math.cos(angle) * radius, Math.sin(angle) * radius * 0.65, (random() - 0.5) * 1.8], i * 3);
      seeds[i] = random();
    }
    const particleGeo = new THREE.BufferGeometry(); geometries.push(particleGeo);
    particleGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute("aScatter", new THREE.BufferAttribute(scatter, 3));
    particleGeo.setAttribute("aSeed", new THREE.BufferAttribute(seeds, 1));
    const uniforms = {
      uAssembly: { value: 0 }, uOpacity: { value: 0 }, uDpr: { value: dpr },
      uTime: { value: 0 }, uPointer: { value: new THREE.Vector2() },
      uInteraction: { value: 0 }, uPointScale: { value: 1 },
    };
    const particlesMaterial = new THREE.ShaderMaterial({
      uniforms, transparent: true, depthWrite: false,
      vertexShader: `attribute vec3 aScatter; attribute float aSeed;
        uniform float uAssembly,uDpr,uTime,uInteraction,uPointScale;
        uniform vec2 uPointer; varying float vSeed,vDepth;
        void main(){
          vec3 p=mix(aScatter,position,uAssembly);
          float loose=1.-uAssembly;
          p.xy+=vec2(sin(aSeed*30.+uTime*.35),cos(aSeed*28.+uTime*.3))*.025*loose;
          vec2 d=p.xy-uPointer; float near=exp(-dot(d,d)*18.);
          p.xy+=d*near*uInteraction*.23;
          p.z+=near*uInteraction*.08;
          vec4 mv=modelViewMatrix*vec4(p,1.);
          gl_Position=projectionMatrix*mv;
          gl_PointSize=(1.7+aSeed*1.9)*uDpr*uPointScale;
          vSeed=aSeed;vDepth=clamp((position.z+.08)*5.,0.,1.);
        }`,
      fragmentShader: `uniform float uOpacity; varying float vSeed,vDepth;
        void main(){
          vec2 p=gl_PointCoord-.5; float r=length(p);
          float alpha=(1.-smoothstep(.34,.5,r))*uOpacity;
          if(alpha<.01)discard;
          vec3 ink=mix(vec3(.055,.13,.095),vec3(.24,.13,.31),vSeed*.7);
          ink=mix(ink,vec3(.34,.43,.30),vDepth*.24);
          float shine=exp(-length(p-vec2(-.15,.18))*11.);
          gl_FragColor=vec4(ink+shine*.11,alpha);
          #include <colorspace_fragment>
        }`,
    });
    materials.push(particlesMaterial);
    const particles = new THREE.Points(particleGeo, particlesMaterial);
    particles.frustumCulled = false; emblem.add(particles);

    // Soft physical grounding without an expensive shadow-map pass.
    const shadowCanvas = document.createElement("canvas"); shadowCanvas.width = shadowCanvas.height = 128;
    const context = shadowCanvas.getContext("2d")!;
    const gradient = context.createRadialGradient(64, 64, 3, 64, 64, 63);
    gradient.addColorStop(0, "rgba(92,76,109,.22)"); gradient.addColorStop(1, "rgba(92,76,109,0)");
    context.fillStyle = gradient; context.fillRect(0, 0, 128, 128);
    const shadowTexture = new THREE.CanvasTexture(shadowCanvas);
    const shadowGeo = new THREE.PlaneGeometry(7, 1.15); geometries.push(shadowGeo);
    const shadowMaterial = new THREE.MeshBasicMaterial({ map: shadowTexture, transparent: true, depthWrite: false });
    materials.push(shadowMaterial);
    const shadow = new THREE.Mesh(shadowGeo, shadowMaterial); shadow.position.set(0, -2.65, -4); scene.add(shadow);

    let frame = 0, disposed = false, width = 1, height = 1, last = 0, activeUntil = performance.now() + 1800;
    const pointer = new THREE.Vector2(), pointerTarget = new THREE.Vector2();
    let hovering = false;
    function resize() {
      width = el.clientWidth; height = el.clientHeight;
      renderer.setSize(width, height);
      camera.left = -5 * width / height; camera.right = 5 * width / height;
      camera.updateProjectionMatrix(); restart();
    }
    function render(now: number) {
      frame = 0;
      if (disposed || document.hidden) return;
      if (now - last < 32) { frame = requestAnimationFrame(render); return; }
      last = now;
      const s = state.current, pose = openingPose(s.phase, s.reduced), { dissolve } = openingProgress(s.phase, 1);
      const reduced = s.reduced;
      pointer.lerp(pointerTarget, 0.12);
      const drift = reduced ? 0 : Math.sin(now * 0.00045) * 0.035;
      const sweep = reduced ? Number(s.phase >= 0.15) : ease((s.phase - 0.015) / 0.205);
      ribbons.visible = s.phase < 0.23;
      strips.forEach((mesh, i) => {
        const settings = ribbonSettings[i];
        const slide = sweep * (14 + i * 1.2) * settings.dir;
        mesh.position.set(settings.x + slide, settings.y + sweep * (i % 2 ? 3 : -3), settings.z);
        mesh.rotation.set(reduced ? 0 : pointer.y * 0.025, drift * (1 - sweep), settings.angle + sweep * settings.dir * 0.12);
        mesh.scale.x = Math.max(0.85, width / height / 1.5);
      });
      const large = width < 600 ? Math.min(3.5, width / height * 6.8) : 4;
      const siteBlend = ease(dissolve);
      const ax = THREE.MathUtils.lerp(s.anchor.x, s.siteAnchor.x, siteBlend);
      const ay = THREE.MathUtils.lerp(s.anchor.y, s.siteAnchor.y, siteBlend);
      const ah = THREE.MathUtils.lerp(s.anchor.height, s.siteAnchor.height, siteBlend);
      const dockX = (ax / width - 0.5) * (10 * width / height);
      const dockY = (0.5 - ay / height) * 10;
      emblem.position.set(dockX * pose.dock, dockY * pose.dock + drift * (1 - pose.dock), 0);
      // The existing transparent brand image has breathing room around its ink.
      // Match that painted area rather than filling the whole image element.
      const scale = THREE.MathUtils.lerp(large, ah * 0.78 / height * 10 / 1.028, pose.dock);
      emblem.scale.setScalar(scale);
      emblem.rotation.set(0.12 * (1 - pose.dock) + (reduced ? 0 : pointer.y * .018 * (1 - pose.dock)),
        -0.32 * (1 - pose.dock) + (reduced ? 0 : pointer.x * .035 * (1 - pose.dock)),
        -0.025 * (1 - pose.dock));
      const markOpacity = pose.dock > 0.999 ? s.logoOpacity : 1;
      reveal.value = reduced ? 1 : pose.solid;
      brandMaterial.opacity = markOpacity;
      edgeMaterial.opacity = markOpacity;
      solid.visible = reveal.value > 0.001;
      particles.visible = !reduced && pose.solid < 1 && s.phase < 0.3;
      uniforms.uAssembly.value = pose.assembly;
      uniforms.uOpacity.value = ease(s.phase / 0.065) * (1 - ease((pose.solid - 0.2) / 0.8));
      uniforms.uTime.value = reduced ? 0 : now * 0.001;
      uniforms.uPointScale.value = Math.min(1, width / 800 + 0.3);
      uniforms.uPointer.value.copy(pointer).multiplyScalar(0.7);
      uniforms.uInteraction.value = hovering && !reduced && pose.assembly > .95 ? 1 : 0;
      shadowMaterial.opacity = (1 - pose.dock) * ease(s.phase / .1);
      shadow.visible = pose.dock < 1;
      renderer.render(scene, camera);
      stage.dataset.brandScene = "ready";
      el.dataset.phase = s.phase < .15 ? "ribbons" : s.phase < .225 ? "particles" : s.phase < .29 ? "solid" : s.phase < .375 ? "docking" : "gallery";
      if (!reduced && s.phase < .375 && (now < activeUntil || hovering)) frame = requestAnimationFrame(render);
    }
    function restart() {
      if (!disposed && !document.hidden && !frame) frame = requestAnimationFrame(render);
    }
    function move(event: PointerEvent) {
      if (state.current.phase >= 0.375 || state.current.reduced) return;
      pointerTarget.set(event.clientX / width * 2 - 1, 1 - event.clientY / height * 2);
      hovering = true; activeUntil = performance.now() + 300; restart();
    }
    function leave() { hovering = false; pointerTarget.set(0, 0); activeUntil = performance.now() + 700; restart(); }
    function visibility() { if (document.hidden) { cancelAnimationFrame(frame); frame = 0; } else restart(); }
    wake.current = restart;
    const observer = new ResizeObserver(resize); observer.observe(el);
    stage.addEventListener("pointermove", move, { passive: true });
    stage.addEventListener("pointerleave", leave);
    document.addEventListener("visibilitychange", visibility);
    resize();
    return () => {
      disposed = true; cancelAnimationFrame(frame); observer.disconnect(); wake.current = () => {};
      stage.removeEventListener("pointermove", move); stage.removeEventListener("pointerleave", leave);
      document.removeEventListener("visibilitychange", visibility);
      geometries.forEach((g) => g.dispose()); materials.forEach((m) => m.dispose());
      environment.dispose(); shadowTexture.dispose(); renderer.dispose(); renderer.domElement.remove();
      delete stage.dataset.brandScene;
    };
  }, [state, wake]);
  return <div ref={host} className="opening-brand-scene" aria-hidden="true" />;
}
