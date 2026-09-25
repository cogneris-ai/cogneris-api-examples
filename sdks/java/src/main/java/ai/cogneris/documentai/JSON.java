/*
 * Cogneris Document AI API
 * The Cogneris Document AI API turns unstructured documents — PDFs, images, scans — into structured JSON.  This document describes the endpoints that are actually deployed. It is written from the running service (`cogneris-api-be`) rather than from a design, so what is listed here is what you can call.  ## Authentication  Every endpoint takes an API key in the `Authorization` header as `Bearer <key>`. Keys begin with `xtkt_live_` (production) or `xtkt_test_` (sandbox); either prefix is accepted before the key is looked up for validation. The key selects the application environment. A recognized prefix alone does not authenticate a request: the key must also be valid and active. Keys are tenant-scoped and cannot cross tenant boundaries. Mint them in the dashboard under **Settings → API keys**.  ## Uploads  The synchronous document endpoints take `multipart/form-data`. There is no fetch-by-URL variant — the file travels in the request body.  - Accepted extensions: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`,   `.bmp`, `.doc`, `.docx` - Maximum size: 10 MB per file, except `/Document/split`, which accepts 500 MB  The asynchronous job endpoints do not take a file. Upload it first to `POST /api/v1/artifacts` — same extensions, same 10 MB limit — and submit the `artifact://` reference it returns.  ## Artifact references  A reference names one stored object. `POST /api/v1/artifacts` returns one, a job submit consumes one as `inputReference`, and a finished job returns one as `outputReference`. `GET /api/v1/artifacts/content` turns either back into bytes.  - References are scoped to the tenant that created them. One belonging to another   tenant is refused as an invalid reference — the answer does not distinguish a   reference that exists elsewhere from one that never existed. - An uploaded reference is **reusable**: one upload can back several jobs. - It expires **7 days** after upload, matching how long a job is retained. The   exact instant is returned as `expiresAt`. Reading it afterwards answers `410`,   which is not `404` — the reference was real, it aged out, and re-requesting it   will never succeed. Upload again. - A job's `outputReference` lives as long as the job does.  ### Two shapes, one of them historical  Everything this API produces today is `artifact://<key>`. Jobs that completed before 2026-09-22 carry a bucket-qualified path instead — `<bucket>/<tenant>/document-jobs/<jobId>/result.json`, sometimes with an `@<version>` suffix. `GET /api/v1/artifacts/content` accepts both, so a reference stored from an older job still resolves for the rest of its life. Treat a reference as opaque: pass back exactly what you were given.  ## Templates  Extraction and classification are driven by the document types and templates configured for your tenant. The platform selects the template from the document itself, so the synchronous `/Document/_*` calls take no template or schema parameter. Use `GET /api/v1/templates` to list the finished templates available to your key before naming one explicitly with `templateId` on `POST /api/v1/document-jobs`. The list is cursor-paginated; pass its `nextCursor` as `cursor` to read the next page.  ## Scopes  Keys carry scopes. The Portal and webhook-endpoint routes check them and answer `403` when the required one is absent; the document endpoints accept any valid key for the tenant without consulting the list. `*` is a real scope meaning full access, and it is what a key receives when it is created without an explicit scope list.  ## Webhooks  A finished asynchronous job can announce itself, so you do not have to poll it. Register an HTTPS endpoint with `POST /api/v1/webhook-endpoints` and it receives a signed `POST` when a job you subscribed to succeeds, fails or is cancelled. The webhook **announces** the result and does not carry it: read the bytes with `GET /api/v1/artifacts/content?reference=<OutputReference>`.  Endpoints are managed with a **production** key holding `webhooks.manage` (or `*`). An endpoint receives your whole account's production events for the events it subscribes to, and events from sandbox jobs are never delivered, so a sandbox key is refused.  Each delivery carries three headers:  - `X-Xtrakt-Event` — the event name, such as `extract.processed`. - `X-Xtrakt-Delivery` — a fresh id per send. It is not a deduplication key. - `X-Xtrakt-Signature` — `t=<unix seconds>,v1=<hex>`, where `v1` is the   HMAC-SHA256 of `<t>.<raw body>` keyed with the endpoint's `whsec_` secret.   Recompute it over the raw bytes, compare in constant time, and reject a `t`   outside your tolerance.  For a job, the body is the job's terminal state. **Its property names are PascalCase**, unlike the rest of this API:  ```json {\"JobId\":\"7c9e6679-7425-40de-944b-e07fc1f90ae7\",\"Operation\":\"Extraction\",  \"Status\":\"succeeded\",\"OutputReference\":\"artifact://document-jobs/7c9e6679-7425-40de-944b-e07fc1f90ae7/result.json\",  \"Stage\":null,\"ProcessedPages\":null,\"TotalPages\":null,\"FailureCode\":null,  \"AttemptCount\":1,\"CompletedAt\":\"2026-09-23T14:02:11.482Z\"} ```  `Status` is `succeeded`, `failed` or `cancelled`, and a cancelled job sends the `.failed` event. `OutputReference` is null unless the job succeeded, and always null for `Redaction`. The synchronous `/Document/_*` calls fire the same event names with their own response as the body; a delivery about a job is the one that has `JobId`. An endpoint with a `body` sends that fixed text **instead of** the payload.  Delivery semantics:  - **A job's outcome never depends on its webhook.** A job that succeeded stays   succeeded when the delivery fails; `GET /api/v1/document-jobs/{jobId}` is the   source of truth. - **One attempt per endpoint, no retry.** A timeout or a non-2xx answer is   recorded and not sent again. Answer `2xx` fast and do the work afterwards, and   reconcile periodically with `GET /api/v1/document-jobs`. - **Duplicates are rare but possible.** Deduplicate on `JobId` plus the event. - Every delivery attempt is metered as webhook usage, successful or not.  ## Rate limits  One shared policy covers every surface in this document, Portal included: **50 requests per API key per fixed 1-minute window**. It is a fixed window rather than a token bucket, so the allowance resets on the minute instead of refilling gradually. Requests over the limit receive `429`.  ## Response envelope  Successful responses from the **document, job and webhook-endpoint** routes share one wrapper: `data` for the payload, `meta` for the status and any messages, and `hasErrors` for a fast failure check. The webhook-endpoint routes send their **errors** as problem documents, described next.  The **Portal** endpoints do not use that wrapper. They return the payload directly, and their errors are RFC 9457 problem documents sent as `application/problem+json`, with a stable `code`, a `correlationId` that is also returned in the `x-correlation-id` header, and a `retryable` flag. Branch on `code`; treat `type` as an opaque identifier.  ## Errors  An error arrives in one of two shapes, and the `Content-Type` says which.  - `application/problem+json` — an RFC 9457 problem document, the same one the   Portal uses. Every route answers this way when the failure happens before your   request is processed: a missing or invalid key (`401`), the rate limit (`429`),   a request refused as malformed or unsafe (`400`), or an unexpected failure   (`500`). - `application/json` — the service envelope with `hasErrors: true` and the   reasons in `meta.errors`. The document, job and artifact routes answer this way   when processing itself fails. Each operation lists the statuses where it does.  Every operation lists `400`, `401`, `403`, `404`, `409`, `429` and `500`, because the API answers each of them in the same shape wherever it occurs. A status on an operation with nothing to miss or conflict with — a `409` on a read, say — is part of that uniform model and not something the operation returns in practice.
 *
 * The version of the OpenAPI document: 2026-09-24
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */


package ai.cogneris.documentai;

import com.fasterxml.jackson.annotation.*;
import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.databind.json.JsonMapper;
import org.openapitools.jackson.nullable.JsonNullableModule;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import ai.cogneris.documentai.model.*;

import java.text.DateFormat;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
public class JSON {
  private ObjectMapper mapper;

  public JSON() {
    mapper = JsonMapper.builder()
        .serializationInclusion(JsonInclude.Include.NON_NULL)
        .disable(MapperFeature.ALLOW_COERCION_OF_SCALARS)
        .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
        .enable(DeserializationFeature.FAIL_ON_INVALID_SUBTYPE)
        .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
        .enable(SerializationFeature.WRITE_ENUMS_USING_TO_STRING)
        .enable(DeserializationFeature.READ_ENUMS_USING_TO_STRING)
        .defaultDateFormat(new RFC3339DateFormat())
        .addModule(new JavaTimeModule())
        .build();
    JsonNullableModule jnm = new JsonNullableModule();
    mapper.registerModule(jnm);
  }

  /**
   * Set the date format for JSON (de)serialization with Date properties.
   *
   * @param dateFormat Date format
   */
  public void setDateFormat(DateFormat dateFormat) {
    mapper.setDateFormat(dateFormat);
  }

  /**
   * Get the object mapper
   *
   * @return object mapper
   */
  public ObjectMapper getMapper() { return mapper; }

  /**
   * Returns the target model class that should be used to deserialize the input data.
   * The discriminator mappings are used to determine the target model class.
   *
   * @param node The input data.
   * @param modelClass The class that contains the discriminator mappings.
   *
   * @return the target model class.
   */
  public static Class<?> getClassForElement(JsonNode node, Class<?> modelClass) {
    ClassDiscriminatorMapping cdm = modelDiscriminators.get(modelClass);
    if (cdm != null) {
      return cdm.getClassForElement(node, new HashSet<Class<?>>());
    }
    return null;
  }

  /**
   * Helper class to register the discriminator mappings.
   */
  @javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaClientCodegen", comments = "Generator version: 7.25.0")
  private static class ClassDiscriminatorMapping {
    // The model class name.
    Class<?> modelClass;
    // The name of the discriminator property.
    String discriminatorName;
    // The discriminator mappings for a model class.
    Map<String, Class<?>> discriminatorMappings;

    // Constructs a new class discriminator.
    ClassDiscriminatorMapping(Class<?> cls, String propertyName, Map<String, Class<?>> mappings) {
      modelClass = cls;
      discriminatorName = propertyName;
      discriminatorMappings = new HashMap<String, Class<?>>();
      if (mappings != null) {
        discriminatorMappings.putAll(mappings);
      }
    }

    // Return the name of the discriminator property for this model class.
    String getDiscriminatorPropertyName() {
      return discriminatorName;
    }

    // Return the discriminator value or null if the discriminator is not
    // present in the payload.
    String getDiscriminatorValue(JsonNode node) {
      // Determine the value of the discriminator property in the input data.
      if (discriminatorName != null) {
        // Get the value of the discriminator property, if present in the input payload.
        node = node.get(discriminatorName);
        if (node != null && node.isValueNode()) {
          String discrValue = node.asText();
          if (discrValue != null) {
            return discrValue;
          }
        }
      }
      return null;
    }

    /**
     * Returns the target model class that should be used to deserialize the input data.
     * This function can be invoked for anyOf/oneOf composed models with discriminator mappings.
     * The discriminator mappings are used to determine the target model class.
     *
     * @param node The input data.
     * @param visitedClasses The set of classes that have already been visited.
     *
     * @return the target model class.
     */
    Class<?> getClassForElement(JsonNode node, Set<Class<?>> visitedClasses) {
      if (visitedClasses.contains(modelClass)) {
        // Class has already been visited.
        return null;
      }
      // Determine the value of the discriminator property in the input data.
      String discrValue = getDiscriminatorValue(node);
      if (discrValue == null) {
        return null;
      }
      Class<?> cls = discriminatorMappings.get(discrValue);
      // It may not be sufficient to return this cls directly because that target class
      // may itself be a composed schema, possibly with its own discriminator.
      visitedClasses.add(modelClass);
      for (Class<?> childClass : discriminatorMappings.values()) {
        ClassDiscriminatorMapping childCdm = modelDiscriminators.get(childClass);
        if (childCdm == null) {
          continue;
        }
        if (!discriminatorName.equals(childCdm.discriminatorName)) {
          discrValue = getDiscriminatorValue(node);
          if (discrValue == null) {
            continue;
          }
        }
        if (childCdm != null) {
          // Recursively traverse the discriminator mappings.
          Class<?> childDiscr = childCdm.getClassForElement(node, visitedClasses);
          if (childDiscr != null) {
            return childDiscr;
          }
        }
      }
      return cls;
    }
  }

  /**
   * Returns true if inst is an instance of modelClass in the OpenAPI model hierarchy.
   *
   * The Java class hierarchy is not implemented the same way as the OpenAPI model hierarchy,
   * so it's not possible to use the instanceof keyword.
   *
   * @param modelClass A OpenAPI model class.
   * @param inst The instance object.
   * @param visitedClasses The set of classes that have already been visited.
   *
   * @return true if inst is an instance of modelClass in the OpenAPI model hierarchy.
   */
  public static boolean isInstanceOf(Class<?> modelClass, Object inst, Set<Class<?>> visitedClasses) {
    if (modelClass.isInstance(inst)) {
      // This handles the 'allOf' use case with single parent inheritance.
      return true;
    }
    if (visitedClasses.contains(modelClass)) {
      // This is to prevent infinite recursion when the composed schemas have
      // a circular dependency.
      return false;
    }
    visitedClasses.add(modelClass);

    // Traverse the oneOf/anyOf composed schemas.
    Map<String, Class<?>> descendants = modelDescendants.get(modelClass);
    if (descendants != null) {
      for (Class<?> childType : descendants.values()) {
        if (isInstanceOf(childType, inst, visitedClasses)) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * A map of discriminators for all model classes.
   */
  private static Map<Class<?>, ClassDiscriminatorMapping> modelDiscriminators = new HashMap<>();

  /**
   * A map of oneOf/anyOf descendants for each model class.
   */
  private static Map<Class<?>, Map<String, Class<?>>> modelDescendants = new HashMap<>();

  /**
    * Register a model class discriminator.
    *
    * @param modelClass the model class
    * @param discriminatorPropertyName the name of the discriminator property
    * @param mappings a map with the discriminator mappings.
    */
  public static void registerDiscriminator(Class<?> modelClass, String discriminatorPropertyName, Map<String, Class<?>> mappings) {
    ClassDiscriminatorMapping m = new ClassDiscriminatorMapping(modelClass, discriminatorPropertyName, mappings);
    modelDiscriminators.put(modelClass, m);
  }

  /**
    * Register the oneOf/anyOf descendants of the modelClass.
    *
    * @param modelClass the model class
    * @param descendants a map of oneOf/anyOf descendants.
    */
  public static void registerDescendants(Class<?> modelClass, Map<String, Class<?>> descendants) {
    modelDescendants.put(modelClass, descendants);
  }

  private static JSON json;

  static {
    json = new JSON();
  }

  /**
    * Get the default JSON instance.
    *
    * @return the default JSON instance
    */
  public static JSON getDefault() {
    return json;
  }

  /**
    * Set the default JSON instance.
    *
    * @param json JSON instance to be used
    */
  public static void setDefault(JSON json) {
    JSON.json = json;
  }
}
