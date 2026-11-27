import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import * as THREE from "three";
// @ts-expect-error The attributed upstream scene is JavaScript.
import Arm from "../src/light-study/objects/Arm.js";

interface Node {
  name?: string;
  children?: number[];
  rotation?: [number, number, number, number];
  translation?: [number, number, number];
}
const bytes = readFileSync(
  new URL("../public/light-study/arm_bones.glb", import.meta.url),
);
const jsonLength = bytes.readUInt32LE(12);
const model = JSON.parse(bytes.subarray(20, 20 + jsonLength).toString()) as {
  nodes: Node[];
};

function skeleton() {
  const root = new THREE.Group();
  // Bounds stand in for the compressed mesh; bone data comes from the real GLB.
  root.add(new THREE.Mesh(new THREE.BoxGeometry(1, 4, 1)));
  const bones = model.nodes.map((node) => {
    const bone = new THREE.Bone();
    bone.name = node.name ?? "";
    if (node.rotation) bone.quaternion.fromArray(node.rotation);
    if (node.translation) bone.position.fromArray(node.translation);
    return bone;
  });
  model.nodes.forEach((node, index) =>
    node.children?.forEach((child) => bones[index].add(bones[child])),
  );
  bones.filter((bone) => !bone.parent).forEach((bone) => root.add(bone));
  return root;
}

describe("Restored hand animation", () => {
  it("loads a real finger skeleton instead of a flat image", () => {
    const names = model.nodes.map((node) => node.name);
    expect(names).toContain("hand");
    for (const finger of ["thumb", "index", "middle", "ring", "pinky"])
      expect(
        names.some((name) => name?.match(new RegExp(`^${finger}\\.?\\d*$`))),
      ).toBe(true);
  });
  it("changes finger and wrist rotations over time on the actual skeleton", () => {
    const arm = new Arm(skeleton());
    expect(arm.fingerBones.length).toBeGreaterThan(10);
    arm.update(0);
    const before = arm.fingerBones.map(
      ({ bone }: { bone: THREE.Bone }) => bone.rotation.x,
    );
    const wrist = arm.handBone.rotation.y;
    arm.update(0.75);
    expect(
      arm.fingerBones.some(
        ({ bone }: { bone: THREE.Bone }, i: number) =>
          Math.abs(bone.rotation.x - before[i]) > 0.001,
      ),
    ).toBe(true);
    expect(Math.abs(arm.handBone.rotation.y - wrist)).toBeGreaterThan(0.001);
  });
});
