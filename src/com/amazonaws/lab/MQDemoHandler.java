package com.amazonaws.lab;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.LambdaLogger;
import com.amazonaws.services.lambda.runtime.RequestStreamHandler;
import com.amazonaws.services.mq.AmazonMQ;
import com.amazonaws.services.mq.AmazonMQClientBuilder;
import com.amazonaws.services.mq.model.ConfigurationId;
import com.amazonaws.services.mq.model.DescribeBrokerRequest;
import com.amazonaws.services.mq.model.DescribeBrokerResult;
import com.amazonaws.services.mq.model.DescribeConfigurationRevisionRequest;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonSyntaxException;

import javax.xml.transform.Source;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import java.io.*;
import java.nio.charset.Charset;
import java.util.Base64;
import java.util.HashMap;

public class MQDemoHandler implements RequestStreamHandler {
    Gson gson = new GsonBuilder().setPrettyPrinting().create();

    @Override
    public void handleRequest(InputStream inputStream, OutputStream outputStream, Context context) throws IOException {
        LambdaLogger logger = context.getLogger();

        BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream, Charset.forName("US-ASCII")));
        PrintWriter writer = new PrintWriter(new BufferedWriter(new OutputStreamWriter(outputStream, Charset.forName("US-ASCII"))));
        try {
            HashMap event = gson.fromJson(reader, HashMap.class);
            logger.log("STREAM TYPE: " + inputStream.getClass().toString());
            logger.log("EVENT TYPE: " + event.getClass().toString());
            writer.write(gson.toJson(event));
            //System.out.println("The event : "+gson.toJson(event));

            logger.log("The account :" + event.get("account").toString());
            if (writer.checkError()) {
                logger.log("WARNING: Writer encountered an error.");
            }
        } catch (IllegalStateException | JsonSyntaxException exception) {
            logger.log(exception.toString());
        } finally {
            reader.close();
            writer.close();
        }
    }

    public String getBrokerConfiguration(String brokerId) {
        DescribeBrokerRequest brokerRequest = new DescribeBrokerRequest();
        brokerRequest.setBrokerId(brokerId);
        AmazonMQ mqClient = AmazonMQClientBuilder.defaultClient();
        DescribeBrokerResult brokerResult = mqClient.describeBroker(brokerRequest);
        ConfigurationId configurationId = brokerResult.getConfigurations().getCurrent();


        System.out.println("Configuration id : "+configurationId.getId());
        DescribeConfigurationRevisionRequest describeConfigurationRevisionRequest = new DescribeConfigurationRevisionRequest();
        describeConfigurationRevisionRequest.setConfigurationId(configurationId.getId());
        describeConfigurationRevisionRequest.setConfigurationRevision(configurationId.getRevision().toString());
        String base64Config=
                mqClient.describeConfigurationRevision(describeConfigurationRevisionRequest).getData();

        byte[] decoded = Base64.getDecoder().decode(base64Config);
        String activeMQXML = new String(decoded);

        //System.out.println("The activemq xml : "+new String(decoded));
        return new String(decoded);

    }

    public static void main(String []args)throws Exception{
        MQDemoHandler noBAutoScaler = new MQDemoHandler();
        String activeMQXML = noBAutoScaler.getBrokerConfiguration("b-972dda01-1f79-4b86-9448-68e4accd5ae9");
        TransformerFactory factory = TransformerFactory.newInstance();


        Source xslt = new StreamSource(new File("./nobtransform.xslt"));
        Transformer transformer = factory.newTransformer(xslt);
        Source text = new StreamSource(new StringReader(activeMQXML));
        StringWriter stringWriter = new StringWriter();

        transformer.transform(text,new StreamResult(stringWriter));

        System.out.println("Transfromed : \n"+stringWriter.getBuffer().toString());
    }
}