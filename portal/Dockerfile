FROM node:20-alpine

WORKDIR /app

# Copia apenas package.json primeiro
COPY package*.json ./

# Instala dependências
RUN npm install

# Copia o restante do projeto
COPY . .

# Garante permissão de execução
RUN chmod -R 755 /app

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
