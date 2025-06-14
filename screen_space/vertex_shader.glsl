void main() {
    fragPos = position;
    fragNorm = normal;
    gl_Position = viewProjectionMatrix * vec4(position, 1.0f);
}
