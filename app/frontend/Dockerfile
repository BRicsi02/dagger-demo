# frontend/Dockerfile
FROM nginx:stable-alpine
COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
