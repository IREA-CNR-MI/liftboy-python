<?xml version="1.0" encoding="UTF-8"?>
<!-- 
    this stylesheet is specific to ISO 19136 metadata and shall be applied right after the default one
    Author: Cristiano Fugazza (fugazza.c@irea.cnr.it)
-->
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="html" encoding="UTF-8" indent="yes" omit-xml-declaration="no"/>
    <!--<xsl:output method="xml" encoding="UTF-8" indent="yes" omit-xml-declaration="no"/>-->

    <xsl:strip-space elements="*" />
    
    <xsl:template match="baseDocument">
        
        <baseDocument>
            
            <xsl:value-of select="text()" disable-output-escaping="no"/>
            
        </baseDocument>        

    </xsl:template>
    
    <!-- remove keyw_voc_contr instances that do not have a URI associated with them -->
    <xsl:template match="//element[represents_element = 'keyw_voc_contr' and not(descendant::item[hasIndex = '1']/codeValue/text())]"/>

    <!-- transform nodes that were temporarily inserted in dummyNode(s) -->
    <xsl:template match="dummyNode">
        <xsl:choose>
            <!-- keyw_voc_contr -> keyw -->
            <xsl:when test="contains(element/id/text(), 'keyw_voc_contr')">
                <xsl:variable name="tail" select="substring-after(element/id/text(), 'keyw_voc_contr')"/>
                
                <element>
                    
                    <xsl:element name="id">
                        <!-- <xsl:value-of select="concat( 'keyw', $tail)" disable-output-escaping="yes"/> -->
                        <xsl:value-of select="concat( 'keyw', $tail)"/>
                    </xsl:element>
                    <xsl:element name="root">
                        <!-- <xsl:value-of select="descendant::root/text()" disable-output-escaping="yes"/> -->
                        <xsl:value-of select="descendant::root/text()"/>
                    </xsl:element>
                    
                    <mandatory>NA</mandatory>
                    <represents_element>keyw</represents_element>
                    <items>
                        <item>
                            
                            <xsl:element name="id">
                                <!-- <xsl:value-of select="concat( concat( 'keyw', $tail), '_1' )" disable-output-escaping="yes"/> -->
                                <xsl:value-of select="concat( concat( 'keyw', $tail), '_1' )"/>
                            </xsl:element>

                            <elementId>keyw</elementId>
                            
                            <xsl:element name="path">
                                <!-- <xsl:value-of select="descendant::path/text()" disable-output-escaping="yes"/> -->
                                <xsl:value-of select="descendant::path/text()"/>
                            </xsl:element>
                            
                            <datatype>string</datatype>
                            <fixed>false</fixed>
                            <useCode/>
                            <useURN/>
                            <outIndex/>
                            
                            <xsl:element name="value">
                                <!-- <xsl:value-of select="descendant::value/text()" disable-output-escaping="yes"/> -->
                                <xsl:value-of select="descendant::value/text()"/>
                            </xsl:element>
                            <xsl:element name="labelValue">
                                <!-- <xsl:value-of select="descendant::labelValue/text()" disable-output-escaping="yes"/> -->
                                <xsl:value-of select="descendant::labelValue/text()"/>
                            </xsl:element>

                            <codeValue/>
                            <urnValue/>
                            <languageNeutral/>
                            <listeningFor>#keyw_1</listeningFor>
                            <isLanguageNeutral/>
                            <datasource/>
                            <hasIndex>1</hasIndex>
                            <field/>
                            <itemId/>
                            <show/>
                            <defaultValue/>
                            <query/>
                        </item>
                    </items>
                </element>                

            </xsl:when>
            <!-- all other empty elements -->
            <xsl:otherwise>
                <xsl:apply-templates select="descendant::node()"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- this should be of no use
    <xsl:template match="@* | node()" mode="rewrite">
        <xsl:param name="old_id" />
        <xsl:param name="new_id" />
        <xsl:choose>
            <xsl:when test="starts-with(local-name(), 'id')">
                
                <id>
                    
                    <xsl:value-of select="concat($new_id, substring-after(text(),$old_id))"/>
                    
                </id>
                                
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy>
                    <xsl:apply-templates select="@* | node()" mode="rewrite"/>
                </xsl:copy>                
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template> -->
    
    <!-- identity template -->
    <xsl:template match="@* | node()">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
