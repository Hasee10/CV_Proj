// Adapted from Cullen Webber, three-volumetric-light. Provenance: ../UPSTREAM.json.
import * as THREE from "three";
import createAsciiMaterial from "../materials/AsciiMaterial";

export default class FloatingObjects extends THREE.Group {
	constructor({
		size = 0.8,
		color = new THREE.Color(0xbfe3ff),
		spinSpeed = 1.25,
		floatSpeed = 1.5,
		floatAmplitude = 0.2,
		morphHold = 3,
		morphDuration = 0.75,
		glowIntensity = 1.2,
		glowDistance = 8,
		cellSize = 10,
	} = {}) {
		super();

		this.cellSize = cellSize;

		this.spinSpeed = spinSpeed;
		this.floatSpeed = floatSpeed;
		this.floatAmplitude = floatAmplitude;
		this.baseY = 0;

		this.morphHold = morphHold;
		this.morphDuration = morphDuration;
		this.cycleIndex = -1;

		const sources = [
			this.#createLogoGeometry(size),
			this.#createLogoGeometry(size),
		];
		const nonIndexed = sources.map((g) => (g.index ? g.toNonIndexed() : g));
		const maxCount = Math.max(
			...nonIndexed.map((g) => g.getAttribute("position").count),
		);
		this.shapes = nonIndexed.map((g) => this.#padToCount(g, maxCount));
		sources.forEach((g) => g.dispose());
		nonIndexed.forEach((g) => g.dispose());

		const geometry = new THREE.BufferGeometry();
		geometry.setAttribute(
			"position",
			new THREE.BufferAttribute(this.shapes[0].positions.slice(), 3),
		);
		geometry.setAttribute(
			"normal",
			new THREE.BufferAttribute(this.shapes[0].normals.slice(), 3),
		);
		geometry.setAttribute(
			"aTargetPosition",
			new THREE.BufferAttribute(this.shapes[1].positions.slice(), 3),
		);
		geometry.setAttribute(
			"aTargetNormal",
			new THREE.BufferAttribute(this.shapes[1].normals.slice(), 3),
		);

		geometry.boundingSphere = new THREE.Sphere(new THREE.Vector3(), size * 2);

		this.mesh = new THREE.Mesh(
			geometry,
			createAsciiMaterial({ color: new THREE.Color(color), cellSize }),
		);

		this.mesh.castShadow = false;
		this.add(this.mesh);

		this.glowIntensity = glowIntensity;
		this.glow = new THREE.PointLight(color, glowIntensity, glowDistance, 2);
		this.add(this.glow);
	}

	#createLogoGeometry(size) {
		// Union outline of the project's angular C bracket and checkmark.
		const outline = [[8,8],[31,8],[31,18],[18,18],[18,46],[26,46],
			[20,40],[26,32],[36,42],[55,15],[63,21],[37,57],[31,51],[31,56],[8,56]];
		const shape = new THREE.Shape();
		outline.forEach(([x,y], index) => {
			const px = (x - 35.5) / 49 * size * 1.6;
			const py = (32.5 - y) / 49 * size * 1.6;
			if (index === 0) shape.moveTo(px, py); else shape.lineTo(px, py);
		});
		shape.closePath();
		const geometry = new THREE.ExtrudeGeometry(shape, {
			depth: size * 0.4, curveSegments: 5, bevelEnabled: true,
			bevelThickness: size * 0.04, bevelSize: size * 0.04, bevelSegments: 2,
		});
		geometry.center();
		return geometry;
	}

	#padToCount(geometry, vertexCount) {
		const pos = geometry.getAttribute("position").array;
		const nor = geometry.getAttribute("normal").array;
		const srcCount = pos.length / 3;

		const positions = new Float32Array(vertexCount * 3);
		const normals = new Float32Array(vertexCount * 3);
		positions.set(pos);
		normals.set(nor);

		for (let v = srcCount; v < vertexCount; v += 3) {
			const src = (v % srcCount) * 3;
			for (let i = 0; i < 3; i++) {
				const dst = (v + i) * 3;
				positions[dst] = pos[src];
				positions[dst + 1] = pos[src + 1];
				positions[dst + 2] = pos[src + 2];
				normals[dst] = nor[src];
				normals[dst + 1] = nor[src + 1];
				normals[dst + 2] = nor[src + 2];
			}
		}

		return { positions, normals };
	}

	#setShapes(fromIndex, toIndex) {
		const geometry = this.mesh.geometry;
		const from = this.shapes[fromIndex];
		const to = this.shapes[toIndex];

		geometry.getAttribute("position").array.set(from.positions);
		geometry.getAttribute("normal").array.set(from.normals);
		geometry.getAttribute("aTargetPosition").array.set(to.positions);
		geometry.getAttribute("aTargetNormal").array.set(to.normals);
		for (const name of [
			"position",
			"normal",
			"aTargetPosition",
			"aTargetNormal",
		]) {
			geometry.getAttribute(name).needsUpdate = true;
		}
	}

	setBasePosition(x, y, z) {
		this.position.set(x, y, z);
		this.baseY = y;
	}

	setCellScale(scale) {
		this.mesh.material.uniforms.uCellSize.value =
			(this.cellSize * Math.min(window.devicePixelRatio, 2)) / scale;
	}

	update(elapsed) {
		const uniforms = this.mesh.material.uniforms;
		uniforms.uTime.value = elapsed;

		const cycle = this.morphHold + this.morphDuration;
		const cycleIndex = Math.floor(elapsed / cycle);
		if (cycleIndex !== this.cycleIndex) {
			this.cycleIndex = cycleIndex;
			const count = this.shapes.length;
			this.#setShapes(cycleIndex % count, (cycleIndex + 1) % count);
		}
		const local = elapsed - cycleIndex * cycle;
		const morph = THREE.MathUtils.clamp(
			(local - this.morphHold) / this.morphDuration,
			0,
			1,
		);
		uniforms.uMorph.value = morph;

		const pulse = morph * (1.0 - morph) * 7.0;
		this.glow.intensity = this.glowIntensity * (1.0 + 0.5 * pulse);

		this.rotation.y = elapsed * this.spinSpeed;

		this.position.y =
			this.baseY + Math.sin(elapsed * this.floatSpeed) * this.floatAmplitude;
	}
}
