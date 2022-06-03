<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:amq="http://activemq.apache.org/schema/core"


                exclude-result-prefixes="amq"
                version="1.0">
    <!-- Identity transform -->
    <xsl:template match="@* | node()">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="amq:networkConnectors">


        <xsl:copy>
        <xsl:apply-templates/>
        <networkConnector xmlns="http://activemq.apache.org/schema/core">Yes .. seems to work</networkConnector>
        </xsl:copy>
        <!--
        <networkConnector xmlns="http://activemq.apache.org/schema/core">Insurance</networkConnector>
        <xsl:copy-of select="."/>

        -->

    </xsl:template>
</xsl:stylesheet>