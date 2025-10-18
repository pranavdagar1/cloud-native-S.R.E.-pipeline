#Use an official Node runtime as the best image
FROM node:18-alpine

#Set working directory int the container
WORKDIR /usr/src/app

#copy package.json and package-lock.json for efficient dependency caching
COPY package*.json ./

#Set environment to production
ENV NODE_ENV=production

#install app depenencies
RUN npm ci --only=production

#copy the rest of the application code
COPY . .

#Expose the port the app run on
EXPOSE 3000

#Define the command to run the app
CMD [ "node", "index.js" ]