// Adapted from Cullen Webber, three-volumetric-light. Provenance: ../UPSTREAM.json.
import * as THREE from "three";
import WebGLContext from "./WebGLContext";
import Scene from "../scenes/Scene";

class Three {
	constructor(container) {
		this.container = container;
		this.context = null;
		this.clock = new THREE.Clock();
		this.lastFrame = -100;
		this.reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
	}

	run() {
		this.context = new WebGLContext(this.container);
		this.context.init();
		this.scene = new Scene();
		this.#animate();
		this.#addResizeListener();
	}

	#animate(now = 0) {
		requestAnimationFrame((time) => this.#animate(time));
		if (document.hidden || now - this.lastFrame < 33) return;
		this.lastFrame = now;
		const delta = Math.min(this.clock.getDelta(), 0.1);
		const elapsed = this.reducedMotion.matches ? 0 : this.clock.elapsedTime;

		this.scene.animate(delta, elapsed);
		this.#render();
	}

	#render() {
		if (!this.context.renderer || !this.scene.scene) return;

		if (this.scene.render) {
			this.scene.render(this.context.renderer);
		} else {
			this.context.renderer.render(this.scene.scene, this.scene.camera);
		}
	}

	#addResizeListener() {
		window.addEventListener("resize", () => this.#onResize());
	}

	#onResize() {
		const { width, height } = this.context.getFullScreenDimensions();
		this.context.onResize(width, height);
		this.scene.onResize(width, height);
	}
}

export default Three;
