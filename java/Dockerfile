# syntax=docker/dockerfile:1
# --- Etapa de compilación: el JDK completo solo existe aquí
FROM eclipse-temurin:21-jdk@sha256:8ad118b146aa92da815b576441acd6b42b38236797ad0b6edc8c200b85bb0734 AS build
WORKDIR /src
COPY src/ src/
RUN mkdir out \
 && javac --release 21 -d out src/App.java \
 && printf 'Main-Class: App\n' > manifest.txt \
 && jar --create --file app.jar --manifest manifest.txt -C out .

# --- Etapa final: distroless con solo el JRE, usuario nonroot
FROM gcr.io/distroless/java21-debian13@sha256:128bd878463537eef7771b50fecf68faace9089f654a2d233f1c4f344e6817d9
WORKDIR /app
COPY --from=build --chown=65532:65532 /src/app.jar app.jar
USER 65532:65532
EXPOSE 8080
# Distroless no trae shell ni curl: la propia app expone --health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["java", "-jar", "app.jar", "--health"]
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]
