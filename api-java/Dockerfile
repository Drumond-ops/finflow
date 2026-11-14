# Imagem do serviço de assinaturas (Java 21 + Spring Boot).
# Duas etapas: a 1ª compila com Maven, a 2ª só roda o .jar (imagem final bem menor).
# Ninguém precisa instalar Java nem Maven na máquina: o Docker faz tudo.

# ---------- Etapa 1: compilar ----------
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app

# Compila e roda os testes; se algum teste falhar, a imagem não é criada.
# Na primeira vez o Maven baixa as bibliotecas (alguns minutos).
COPY pom.xml .
COPY src ./src
RUN mvn -B -q package

# ---------- Etapa 2: rodar ----------
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/target/servico-assinaturas.jar app.jar

EXPOSE 8081
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
