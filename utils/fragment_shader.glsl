void main() {
    vec3 normal = normalize(fragNorm);
    vec3 toLight = isDirectionalLight ? normalize(light - fragPos) : light;
    float normalAmount = dot(normal, toLight);

    vec3 v = normalize(toLight - normalAmount * normal);
    vec3 u = cross(normal, v);
    vec3 direction = cos(orientationOffset) * u + sin(orientationOffset) * v;
    const float eps = 0.001f;
    vec4 ppClip = viewProjectionMatrix * vec4(fragPos + eps * direction, 1.0f);
    vec4 pmClip = viewProjectionMatrix * vec4(fragPos - eps * direction, 1.0f);
    vec2 dirScreen = ppClip.xy / ppClip.w - pmClip.xy / pmClip.w;

    float orientation = atan(dirScreen.y, dirScreen.x);
    orientation = isnan(orientation) ? 0.0f : orientation;

    float depth = length(fragPos - cameraPosition);
    float value = max(normalAmount, 0.0f);

    fragColor = vec4(depth, orientation, value, 1.0f);
}
