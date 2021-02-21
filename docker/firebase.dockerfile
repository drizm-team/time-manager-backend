FROM andreysenov/firebase-tools:9.4.0

COPY ["firebase.json", ".firebaserc", ".firebasekey", "/"]

COPY ["./docker/firebase-entrypoint.sh", "/firebase-entrypoint.sh"]

USER root
RUN chmod +x /firebase-entrypoint.sh
RUN sed -i -e 's/\r$//' /firebase-entrypoint.sh

ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-static /tini
RUN chmod +x /tini

USER node

ENTRYPOINT ["/tini", "--"]
CMD ["/firebase-entrypoint.sh"]
EXPOSE 4000 8080
